# Demo Script (2 minutes)

## Setup (15s)
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
# set OPENAI_API_KEY
```

## Run (60s)
```sh
audit run examples/vuln_app --autofix
```

## Talk Track (45s)
- “Red Team scans the code and produces evidence-based findings.”
- “Blue Team proposes minimal patches.”
- “Arbiter validates with bandit/ruff/pytest and a post-fix reattack scan.”
- “We generate a report with a scorecard comparing baseline vs multi-agent loop.”

## Show Artifacts (30s)
- `runs/<run_id>/findings.json`
- `runs/<run_id>/patches.json`
- `runs/<run_id>/verification.json`
- `runs/<run_id>/REPORT.md`
