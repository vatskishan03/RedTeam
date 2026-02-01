import { NextRequest } from 'next/server';
import { spawn } from 'child_process';
import { createInterface } from 'readline';
import { mkdtemp, writeFile, rm } from 'fs/promises';
import { existsSync } from 'fs';
import os from 'os';
import path from 'path';

export const runtime = 'nodejs';

const SUPPORTED_LANGUAGES = new Set(['python', 'javascript', 'typescript']);
const EXTENSION_MAP: Record<string, string> = {
  python: 'py',
  javascript: 'js',
  typescript: 'ts',
};

function findRepoRoot(): string {
  const candidates = [process.cwd(), path.resolve(process.cwd(), '..')];
  for (const candidate of candidates) {
    const auditPath = path.join(candidate, 'src', 'audit');
    const scriptPath = path.join(candidate, 'scripts', 'stream_audit.py');
    if (existsSync(auditPath) && existsSync(scriptPath)) {
      return candidate;
    }
  }
  return process.cwd();
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');
  const language = (searchParams.get('language') || 'python').toLowerCase();

  if (!code) {
    return new Response(JSON.stringify({ error: 'No code provided' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (!SUPPORTED_LANGUAGES.has(language)) {
    return new Response(JSON.stringify({ error: `Unsupported language: ${language}` }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const repoRoot = findRepoRoot();
  const pythonBin = process.env.PYTHON_BIN || path.join(repoRoot, '.venv', 'bin', 'python3');
  const scriptPath = path.join(repoRoot, 'scripts', 'stream_audit.py');

  const tempRoot = await mkdtemp(path.join(os.tmpdir(), 'redteam-'));
  const extension = EXTENSION_MAP[language] || 'txt';
  const targetFile = path.join(tempRoot, `snippet.${extension}`);
  await writeFile(targetFile, code, 'utf-8');

  const useHeuristic = !process.env.OPENAI_API_KEY;
  const args = [scriptPath, '--path', tempRoot];
  if (useHeuristic) {
    args.push('--heuristic');
  }

  const env = {
    ...process.env,
    PYTHONPATH: [path.join(repoRoot, 'src'), process.env.PYTHONPATH || ''].filter(Boolean).join(path.delimiter),
  };

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      let closed = false;

      const sendEvent = (data: object) => {
        if (closed) return;
        try {
          const message = `data: ${JSON.stringify(data)}\n\n`;
          controller.enqueue(encoder.encode(message));
        } catch {
          // Controller already closed, ignore
        }
      };

      const closeStream = () => {
        if (closed) return;
        closed = true;
        try {
          controller.close();
        } catch {
          // Already closed
        }
      };

      const child = spawn(pythonBin, args, {
        cwd: repoRoot,
        env,
      });

      const cleanup = async () => {
        try {
          await rm(tempRoot, { recursive: true, force: true });
        } catch {
          // Ignore cleanup errors.
        }
      };

      request.signal.addEventListener('abort', () => {
        child.kill('SIGTERM');
        cleanup();
        closeStream();
      });

      const rl = createInterface({ input: child.stdout });
      rl.on('line', (line) => {
        if (!line.trim()) {
          return;
        }
        try {
          const data = JSON.parse(line);
          sendEvent(data);
        } catch {
          sendEvent({ type: 'error', message: 'Failed to parse audit output.' });
        }
      });

      child.stderr.on('data', (chunk) => {
        const text = chunk.toString().trim();
        if (text) {
          sendEvent({ type: 'agent_message', agent: 'arbiter', content: text, messageType: 'text' });
        }
      });

      child.on('close', async (code) => {
        if (code !== 0) {
          sendEvent({ type: 'error', message: 'Audit process failed.' });
        }
        sendEvent({ type: 'done' });
        await cleanup();
        closeStream();
      });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
