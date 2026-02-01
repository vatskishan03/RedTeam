# Adversarial Red Team Code Auditor

Your code gets attacked by an AI hacker before it ships - and the fix is validated by making sure the hacker can't break it.

Built for OpenAI Hackathon 2026 (Track 3: Multi-Agent Systems & Workflows).

## Demo (2 minutes)

Watch the demo video: https://drive.google.com/file/d/1-Pg42GmlLAl7GVjZ308Z4U43e7y6nhus/view?usp=sharing

<p align="center">
  <a href="https://drive.google.com/file/d/1-Pg42GmlLAl7GVjZ308Z4U43e7y6nhus/view?usp=sharing">
    <img
      src="https://drive.google.com/thumbnail?id=1-Pg42GmlLAl7GVjZ308Z4U43e7y6nhus&sz=w1200"
      alt="Demo video thumbnail"
      width="900"
    />
  </a>
</p>

## What It Does

This repo implements a **multi-agent adversarial security audit loop**:

- **Attacker (Red Team)**: finds vulnerabilities and describes concrete exploitation paths.
- **Defender (Blue Team)**: proposes minimal patches (unified diffs) per finding.
- **Arbiter**: validates fixes by re-attacking and checking tool signals; continues for multiple rounds until approved (or max rounds).
- **Reporter**: generates a professional Markdown report for the final state.

The key property: **fixes are validated by trying to break them again**.

## Architecture

- **Backend (Python + FastAPI)**: runs the pipeline and streams structured events over SSE.
  - Entry: `src/audit/server.py` (`POST /audit/start`, `GET /audit/stream/{run_id}`)
- **Frontend (Next.js)**: live UI consuming SSE and rendering timeline + per-agent cards.
  - Entry: `UI/src/app/page.tsx`

Run artifacts are written to `runs/<run_id>/` for debugging (ignored by git).

## Local Development

Backend + CLI:
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set OPENAI_API_KEY in .env
pip install -e .

# run full pipeline on the demo app
audit run examples/vuln_app --autofix
```

UI (dev):
```sh
cd UI
npm install
npm run dev
```

Prod-like split mode (UI -> API):
```sh
# terminal 1: backend
uvicorn audit.server:app --reload --host 0.0.0.0 --port 8000

# terminal 2: UI
cd UI
NEXT_PUBLIC_AUDIT_API_URL=http://localhost:8000 npm run dev
```

## Deployment (Render + Vercel)

Backend (Render):
- Deploy using `render.yaml`
- Set these env vars:
  - `OPENAI_API_KEY`
  - `CORS_ORIGINS=https://red-team-one.vercel.app` (lock the API to your UI origin)

Frontend (Vercel):
- Root directory: `UI`
- Env var:
  - `NEXT_PUBLIC_AUDIT_API_URL=https://<your-render-service>.onrender.com`

## Security Notes

- The backend enforces **Origin allowlisting** (not `*`) to prevent arbitrary websites from driving your API via browsers.
- Never commit secrets. Use `.env` locally and Vercel/Render env vars in production.
