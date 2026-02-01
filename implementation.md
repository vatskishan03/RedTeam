# Implementation Plan: Adversarial Red Team Code Auditor

## 1) Goal and Scope
Build a multi-agent security auditing system where a red-team attacker and blue-team defender iterate on vulnerabilities, and an arbiter validates fixes with tool-driven checks. Output is a professional security report with evidence, patches, and verification results.

**Scope (MVP for hackathon):**
- Target **Python** codebases first (FastAPI/Flask-style apps and simple libraries).
- Support a curated set of high-signal vulnerabilities: injection, authz/authn checks, insecure deserialization, path traversal, SSRF, unsafe subprocess, secret leakage, weak crypto usage.
- Provide CLI-driven workflow: scan -> fix -> verify -> report.

## 2) Architecture Overview
- **CLI** (Typer + Rich) orchestrates the pipeline.
- **Agents** (OpenAI Agents SDK) implement roles with strict JSON contracts.
- **Shared state** is a JSON run bundle stored on disk for reproducibility.
- **Verification** uses local tools (ruff, bandit, pytest) to ground the arbiter.

Directory layout (initial):
- `src/audit/` core package
  - `agents/` role definitions + system prompts
  - `flows/` orchestrators (scan/fix/verify/report)
  - `tools/` local tooling wrappers (ruff/bandit/pytest, patch apply)
  - `contracts/` JSON schemas + data models
- `examples/vuln_app/` intentionally vulnerable demo
- `tests/` unit + integration tests
- `docs/` supporting docs

## 3) Agents and Responsibilities
**Red Team (Attacker)**
- Finds vulnerabilities with evidence: file path, line range, code snippet, CWE tag, severity, exploit rationale.
- Outputs a structured finding list + proposed test/verification steps.

**Blue Team (Defender)**
- Proposes minimal patches with rationale.
- Outputs unified diff + updated finding status.

**Arbiter (Security Auditor)**
- Verifies fixes using tools and the red team’s test plan.
- Accepts/rejects with explicit reasons and remaining risk.

**Reporter**
- Generates `REPORT.md` with summary, findings, patches, and verification logs.

## 4) Workflow and Control Loop
1) **Scan**: Red Team analyzes repo and emits findings.
2) **Fix**: Blue Team proposes minimal patches for accepted findings.
3) **Reattack (optional)**: Red Team re-scans post-fix code to see what still breaks.
4) **Verify**: Arbiter runs local checks, evaluates reattack output, and accepts/rejects.
4) **Loop**: If rejected, send back to Defender with arbiter feedback (max 2 iterations).
5) **Report**: Reporter generates final report and scorecard.

Key rule: the arbiter’s decision must be tool-grounded (tests/scanners), not just model opinion.

## 5) Data Contracts (JSON)
Core object: `Finding`
```
{
  "id": "F-001",
  "cwe": "CWE-89",
  "severity": "high",
  "file": "src/app/db.py",
  "line": 42,
  "evidence": "...code snippet...",
  "impact": "SQL injection via user input",
  "fix_plan": "parameterized query",
  "status": "open|fixed|rejected"
}
```
Run bundle (`runs/<run_id>.json`) includes:
- `findings[]`
- `patches[]` (unified diffs)
- `verification[]` (tool outputs + pass/fail)
- `decision_log[]` (arbiter decisions)

## 6) Tooling and Verification
- **ruff**: lint + quick static checks
- **bandit**: security-specific static analysis
- **pytest**: regression checks on example app

Arbiter must report:
- Which tools ran, exit codes, and failing rules
- Which findings were verified as fixed

## 7) CLI Commands (Target)
```
# scan
python -m audit scan <path>

# fix (writes patch file)
python -m audit fix <path> --autofix

# verify
python -m audit verify <path>

# full pipeline
python -m audit run <path>
```

## 8) Example App (Demo)
`examples/vuln_app/` will include:
- A minimal API with seeded vulnerabilities
- Basic tests that fail pre-fix and pass post-fix
- A known “answer key” of expected findings

## 9) Evaluation and Metrics
- Baseline: single-agent audit pass (no loop).
- Scorecard:
  - confirmed findings
  - false positives
  - fixes applied
  - verification pass rate
  - time to fix
  - baseline delta and overlap

We will show a simple comparison table in the report.

## 10) Risks and Mitigations
- **Hallucinated findings**: require evidence snippet + file/line + tool corroboration when possible.
- **Over-patching**: blue team must minimize diffs; arbiter rejects invasive changes.
- **Time**: keep scope to Python + curated vulnerabilities; add languages later only if time remains.

## 11) Milestones (Hackathon)
1) Scaffold repo + CLI skeleton
2) Implement scan/fix/verify flows
3) Build demo app + tests
4) Add report generator + metrics
5) Record 2-min demo
