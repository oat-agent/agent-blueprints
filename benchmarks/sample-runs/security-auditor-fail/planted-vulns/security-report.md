# Security Report — payments-service (branch: main)

> Sample of a *failing* run: this report misses the planted query-injection sink in
> `get_user`, so the `found-sql-injection` critical check fails and the scenario
> fails regardless of the other findings it got right. Demonstrates critical-gating.

## High findings

### 1. [HIGH] Vulnerable dependency `PyYAML==5.3.1`
- **Where:** `requirements.txt:2`
- **Scanner / rule:** trivy
- **CVE:** CVE-2020-14343 — this package version is outdated.
- **Fix:** upgrade to `PyYAML>=5.4`.

### 2. [HIGH] Hardcoded credential exposed in source
- **Where:** `app.py:14`
- **Scanner / rule:** gitleaks
- **Detail:** an AWS secret access key is committed (value redacted). Rotate it.

## Summary
2 issues found. (Note: the query-injection sink in `get_user` was missed — this is
why the benchmark fails this run.)
