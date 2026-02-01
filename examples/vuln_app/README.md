# Vulnerable Demo App

This folder contains intentionally vulnerable Python code used for demos and evaluation.

Seeded issues include:
- SQL injection via string-formatted query
- Insecure deserialization with pickle
- Shell injection with `subprocess.run(..., shell=True)`
- Weak hashing using MD5
- Unsafe YAML load
- Path traversal via direct path join

Run the auditor against this folder:

```sh
audit run examples/vuln_app --autofix
```
