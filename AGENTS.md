# Repository Guidelines

This repo is a multi-agent security auditor (Python) with a live streaming UI (Next.js). Keep changes demo-first: the attacker/defender/arbiter loop must work end-to-end.

## Project Structure & Module Organization

- `src/audit/agents/`: LLM agent wrappers + prompts (red/blue/arbiter/reporter).
- `src/audit/flows/`: pipeline orchestration (`scan` -> `fix` -> `verify` -> `report`).
- `src/audit/tools/`: patch application, linters, file context, OpenAI client.
- `scripts/stream_audit.py`: SSE-friendly runner consumed by the UI.
- `UI/`: Next.js frontend and the `/api/audit` SSE bridge.
- `runs/`: generated run artifacts (do not commit).

## Build, Test, and Development Commands

Python (recommended):
```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
audit run examples/vuln_app --autofix
```

UI:
```sh
cd UI
npm install
npm run dev
```

Standalone stream runner:
```sh
PYTHONPATH=src python3 scripts/stream_audit.py --path examples/vuln_app --max-rounds 3
```

## Coding Style & Naming Conventions

- Python: 4 spaces; keep ruff line length (100) and avoid unnecessary refactors.
- JS/TS: 2 spaces; keep UI changes in `UI/src/components` and `UI/src/hooks`.
- Naming: `snake_case` (Python), `camelCase` (TS/JS), `kebab-case` (dirs).

## Testing Guidelines

- Backend: `pytest` (see `tests/`).
- Lint/security: `ruff check src` and `bandit -r src` (if installed).
- Add a regression test for every pipeline bug (patch apply, re-attack, verdict sync).

## Commit & Pull Request Guidelines

- Follow Conventional Commits (matches existing history): `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
- PRs: include repro steps (sample snippet), expected vs actual, and UI screenshots/GIFs when applicable.

## Security & Configuration Tips

- Never commit secrets; use `.env` locally (see `.env.example`).
- Key env vars: `OPENAI_API_KEY`, `OPENAI_MODEL`, `AUDIT_MAX_ROUNDS`, `AUDIT_EXTENSIONS`.
