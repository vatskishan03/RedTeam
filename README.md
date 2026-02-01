# Adversarial Red Team Code Auditor

Your code gets attacked by an AI hacker before it ships — and the fix is validated by making sure the hacker can't break it.

## Quickstart

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set OPENAI_API_KEY in .env

# install the CLI
pip install -e .

# run the full pipeline on the demo app
audit run examples/vuln_app --autofix
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

## Notes

- The tool writes run artifacts to `runs/`.
- Works best on small Python codebases or the demo app.
