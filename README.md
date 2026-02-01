# Adversarial Red Team Code Auditor

Your code gets attacked by an AI hacker before it ships — and the fix is validated by making sure the hacker can't break it.

## Architecture (Deployable)

- **Backend (Python)**: runs the multi-agent pipeline + streams events over SSE (Render).
- **Frontend (Next.js)**: UI that consumes SSE and renders the 4-agent loop (Vercel).

## Quickstart

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set OPENAI_API_KEY in .env

# install the CLI
pip install -e .

# run the full pipeline on the demo app
audit run examples/vuln_app --autofix
```

## Local UI (Two Options)

1) **All-local (dev only)**: run the UI and use the Next.js `/api/audit` route (spawns Python locally).
```sh
cd UI
npm install
npm run dev
```

2) **Split mode (prod-like)**: run the Python API, then point the UI to it.
```sh
# backend API
uvicorn audit.server:app --reload --host 0.0.0.0 --port 8000

# UI (in a separate terminal)
cd UI
NEXT_PUBLIC_AUDIT_API_URL=http://localhost:8000 npm run dev
```

## CLI

```sh
# scan only
audit scan <path>

# propose fixes (writes patch file)
audit fix <path> --autofix

# verify fixes using local tools
audit verify <path>

# full pipeline

audit run <path> --autofix

# disable baseline comparison
audit run <path> --no-baseline

# disable post-fix reattack scan
audit run <path> --no-reattack

# heuristic-only mode (no API)
audit run <path> --heuristic
```

## What This Does

- Red Team agent finds vulnerabilities with evidence
- Blue Team agent proposes minimal patches
- Arbiter verifies with tools (bandit/ruff/pytest)
- Reporter generates `REPORT.md`

## Demo App

See `examples/vuln_app/` for a small intentionally vulnerable project.

## Demo Script

- `docs/DEMO.md` for the 2-minute walkthrough
- `scripts/demo.sh` for a quick local run

## Notes

- The tool writes run artifacts to `runs/`.
- Works best on small Python codebases or the demo app.

## Deploy (Render + Vercel)

- **Render (backend)**: deploy the repo as a Python web service using `render.yaml`.
  - Start command: `uvicorn audit.server:app --host 0.0.0.0 --port $PORT`
  - Set `OPENAI_API_KEY` + (recommended) `CORS_ORIGINS` to your Vercel domain.
- **Vercel (UI)**: deploy `UI/` as a Next.js project.
  - Set `NEXT_PUBLIC_AUDIT_API_URL` to your Render service URL.
