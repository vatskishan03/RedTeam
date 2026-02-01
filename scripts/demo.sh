#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Set OPENAI_API_KEY in .env before running."
  exit 1
fi

audit run examples/vuln_app --autofix
