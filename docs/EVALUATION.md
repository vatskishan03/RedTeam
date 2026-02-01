# Evaluation and Scorecard

We compare the multi-agent loop against a baseline single-pass red-team scan.

## Metrics
- Findings total
- Fixed / Rejected
- Fix rate
- Tools pass (bandit/ruff/pytest)
- Baseline total
- Delta vs baseline
- Baseline overlap

## Why This Matters
The baseline simulates a single-agent audit without adversarial validation. The multi-agent loop should:
- Catch more true positives
- Reduce hallucinations via verification
- Provide stronger confidence via reattack + tools
