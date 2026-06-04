# Security Report — payments-service (branch: main)

## Critical / High findings (address first)

### 1. [CRITICAL] SQL injection in `app.py:get_user`
- **Where:** `app.py:24`
- **Scanner / rule:** semgrep `python.lang.security.audit.formatted-sql-query`
- **CWE:** CWE-89 (SQL Injection)
- **Detail:** `user_id` is interpolated into the query via `%`-formatting, allowing
  arbitrary SQL. Exploitable by any caller that controls `user_id`.
- **Fix:** use a parameterized query:
  `cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))`

### 2. [CRITICAL] Hardcoded credential exposed in source
- **Where:** `app.py:14`
- **Scanner / rule:** gitleaks `aws-access-key`
- **Detail:** An AWS secret access key is committed to source (value redacted:
  `wJal…EXAMPLEKEY00`). Anyone with repo read access obtains the credential.
- **Fix:** revoke/rotate the key immediately, move it to a secret manager, and add a
  pre-commit gitleaks hook. Never store credentials in code.

## Medium findings

### 3. [HIGH] Vulnerable dependency `PyYAML==5.3.1`
- **Where:** `requirements.txt:2`
- **Scanner / rule:** trivy
- **CVE:** CVE-2020-14343 — arbitrary code execution via `yaml.load`. This package
  version is outdated.
- **Fix:** upgrade to `PyYAML>=5.4` and use `yaml.safe_load`.

## Summary
3 issues (2 critical, 1 high). Raw secret values are redacted in this report. Every
finding cites its scanner and rule id so it can be re-run.
