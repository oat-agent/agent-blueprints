# Benchmarks — Overview

This repo ships a benchmark harness that evaluates the agent templates two ways. The
full methodology, scoring math, and check reference live in
[`../benchmarks/README.md`](../benchmarks/README.md); this page is the short version.

## Why two layers

A template can be perfectly well-formed yet produce bad work, and vice versa. So we
measure both:

| Layer | Question | Runs an agent? | Where |
|---|---|---|---|
| **Static validation** | Is the template well-formed, factory-valid, and rigorous? | No | `benchmarks/framework/static_validator.py` |
| **Behavioral scoring** | Did the agent's *output* actually do the job, safely? | Yes | `benchmarks/framework/scorer.py` |

Static validation is aligned to the **real OAT factory** (`internal/factory/` on the
`feature/agent-factory` branch of `open-agent-teams`): it enforces the same rules the
factory's `Validate()` does, so a template that scores well here will actually
instantiate. Notably, the factory's success conditions only understand
`file_exists`/`command_success` — semantic conditions like `test_coverage` are
ignored at instantiation time, which is exactly why the behavioral layer exists.

## Install

```bash
pip install -r benchmarks/requirements.txt   # just PyYAML
```

## Layer 1 — validate every template

```bash
# Markdown scorecard for all 53 templates + registry + coverage findings
python -m benchmarks.framework.cli validate

# JSON (for dashboards / CI)
python -m benchmarks.framework.cli validate --format json --out scorecard.json

# CI gate: fail the build on any major+ finding or sub-80 score
python -m benchmarks.framework.cli validate --min-score 80 --fail-on major
```

Scoring: start at 100, subtract per finding — `critical` −20, `major` −7.5,
`minor` −2.5, `info` 0. Grades: A ≥90, B ≥80, C ≥70, D ≥60, else F.

## Layer 2 — score an agent's output

Each agent has a suite at `benchmarks/suites/<category>/<agent>.benchmark.yaml`
defining scenarios and a weighted, domain-specific rubric. Run the agent once per
scenario, drop its output in `<outputs>/<scenario_id>/`, then:

```bash
python -m benchmarks.framework.cli score \
  --suite benchmarks/suites/security/security-auditor.benchmark.yaml \
  --outputs benchmarks/sample-runs/security-auditor-pass
```

Worked sample runs live in `benchmarks/sample-runs/` and starting fixtures (with
planted problems the agent must find) live in `benchmarks/fixtures/`.

### Scoring math

```
scenario_score = Σ(weight × check_score) / Σ(weight)     # over non-skipped checks
scenario_passed = scenario_score ≥ pass_threshold AND no critical check failed
suite_score     = mean(scenario_score)
```

- **`critical` checks are hard gates** — failing one fails the scenario regardless of
  the rest (e.g. leaking a secret, breaking the build, a migration with no rollback).
- **Skipped checks** (a missing CLI, or `llm_rubric` with no judge configured) are
  excluded from the denominator so runs stay reproducible offline.

## Authoring / changing a suite

See [`../benchmarks/schema/benchmark-suite.schema.yaml`](../benchmarks/schema/benchmark-suite.schema.yaml)
for the grammar and the full check-type table, then validate:

```bash
python -m benchmarks.framework.cli lint-suites --strict
```

## Tests

```bash
python -m unittest discover -s benchmarks/tests
```
