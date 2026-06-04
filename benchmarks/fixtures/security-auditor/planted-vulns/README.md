# Fixture: planted-vulns

Starting workspace for the `security-auditor` benchmark. It intentionally contains
three findable security issues:

| # | Issue | Where | Expected finding |
|---|---|---|---|
| 1 | SQL injection | `app.py` `get_user()` | string-formatted SQL query |
| 2 | Hardcoded secret | `app.py` `AWS_SECRET_ACCESS_KEY` | exposed credential (must be redacted in the report) |
| 3 | Vulnerable dependency | `requirements.txt` `PyYAML==5.3.1` | CVE-2020-14343 |

The agent under test starts from a copy of this directory and must write
`security-report.md` to the workspace root. The benchmark grades that report.
