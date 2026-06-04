# Agent Blueprints Benchmark

A benchmark harness for evaluating OAT agent templates. It answers two distinct
questions, because a template can be *well-defined* yet *behave badly*, and vice versa:

| Layer | Question | Needs an agent run? | Cost |
|---|---|---|---|
| **1. Static validation** | Is this template well-formed, complete, and rigorous? | No | Cheap — gate every PR |
| **2. Behavioral scoring** | Did the agent actually produce correct, safe, useful output? | Yes | Per-run |

Each agent *type* gets its own behavioral rubric, because "good output" means
something completely different for a `security-auditor` (found the real CVE, leaked
no secrets) than for an `api-builder` (OpenAPI validates, endpoints respond, coverage
>80%) or an `orchestrator` (decomposed the goal, dispatched to the right workers,
produced a coherent plan).

```
benchmarks/
  framework/        # the harness (pure Python, PyYAML only)
  suites/<cat>/<agent>.benchmark.yaml   # one rubric per agent type
  fixtures/<agent>/<scenario>/          # starting workspaces / planted issues
  schema/benchmark-suite.schema.yaml    # the suite file format
  tests/            # unit tests for the harness
```

## Quick start

```bash
pip install -r benchmarks/requirements.txt

# Layer 1 — score every template definition (markdown table + findings)
python -m benchmarks.framework.cli validate

# Gate a PR: fail if anything is below 80 or has a major+ finding
python -m benchmarks.framework.cli validate --min-score 80 --fail-on major

# Lint the suites themselves
python -m benchmarks.framework.cli lint-suites --strict

# Layer 2 — score an agent's outputs against its suite
python -m benchmarks.framework.cli score \
    --suite benchmarks/suites/security/security-auditor.benchmark.yaml \
    --outputs runs/security-auditor/        # contains <scenario_id>/ subdirs
```

## Layer 1: static validation

`validate` parses every `templates/*/*.yaml` and scores it 0–100 by subtracting
weighted penalties for findings:

| Severity | Penalty | Examples |
|---|---|---|
| `critical` | 20 | unparseable YAML, missing `prompt.system`, missing `metadata` |
| `major` | 7.5 | `base.type` not allowed, no machine-verifiable success condition, registry/file mismatch |
| `minor` | 2.5 | short system prompt, no task-template variables, missing tags, no benchmark suite |
| `info` | 0 | unpinned tool version, semantic success conditions that need a behavioral suite |

It also checks repo-wide invariants:

- **Registry consistency** — every `registry.yaml` entry points to a real file; every
  template file is registered; names match paths; `stability`/`verified` are valid.
- **Suite coverage** — every template has a matching behavioral suite.

`grade`: A ≥90, B ≥80, C ≥70, D ≥60, else F.

## Layer 2: behavioral scoring

A **suite** (`<agent>.benchmark.yaml`) targets one template and defines one or more
**scenarios**. A scenario provides `inputs` (values for the template's
`task_template` variables), an optional `workspace` fixture used as the agent's
starting repo, a `pass_threshold`, and a list of weighted **checks**.

You run the agent once per scenario, collecting its output into
`<outputs>/<scenario_id>/`, then `score` grades those directories.

### Scoring math

```
scenario_score = Σ(weight × check_score) / Σ(weight)      # over non-skipped checks
scenario_passed = scenario_score ≥ pass_threshold AND no critical check failed
suite_score    = mean(scenario_score)
suite_passed   = every scenario passed
```

- **Critical checks** are hard gates: if one fails, the scenario fails and its score
  is clamped below the pass threshold, no matter how many other checks passed. Use
  `critical: true` for safety-critical invariants (e.g. "did not leak secrets",
  "build still compiles", "no destructive migration without a rollback").
- **Skipped checks** (e.g. `command_*` when a binary is missing, or `llm_rubric` with
  no judge configured) are excluded from the denominator so a suite stays meaningful
  offline. Coverage gaps show up as `skipped` in the scorecard, never as silent passes.
- A **missing scenario output directory** scores 0 with a critical failure — a
  no-show is the worst outcome, not an excused absence.

### Check types

Deterministic checks (always available):

| type | params | passes when |
|---|---|---|
| `file_exists` / `dir_exists` | `path` | the path exists |
| `file_glob` | `pattern`, `min_matches` | ≥ N files match |
| `file_contains` | `path`, `pattern`, `min_count`, `ignore_case` | regex matches ≥ N times |
| `file_not_contains` | `path`, `pattern` | regex does **not** match (great for "no TODOs", "no secrets") |
| `no_secrets` | `globs`, `extra_patterns` | no AWS/GitHub/Slack/PEM-style secrets in scanned files |
| `json_valid` / `yaml_valid` | `path` | file parses |
| `json_path` | `path`, `query`, `op`, `value` | `a.b[0].c` resolves and compares (`eq/ne/gt/gte/lt/lte/contains/exists`) |
| `metric_threshold` | `path`, `key`, `op`, `value` | a numeric metric the agent reported meets a threshold |
| `command_success` | `command`, `cwd`, `timeout` | exit code 0 (e.g. `pytest`, `openapi-spec-validator`) |
| `command_output_matches` | `command`, `pattern` | command output matches a regex |

Graded check (pluggable):

| type | params | behavior |
|---|---|---|
| `llm_rubric` | `criteria`, `weight` | scored by an LLM-as-judge if one is wired into `CheckContext.judge`; otherwise **skipped** (recorded, not failed) so deterministic runs stay reproducible |

### Why this design

- **Deterministic-first.** The backbone of every rubric is machine-checkable so
  scores are reproducible in CI and not at the mercy of a judge model's mood.
- **Domain-specific.** Generic "did it write a file" checks are necessary but not
  sufficient. Each suite plants a real problem (a SQL-injection sink, a flaky test, a
  N+1 query, a missing rollback) and verifies the agent *actually addressed it*.
- **Safety as a gate, not a score.** Leaking a secret or breaking the build can't be
  averaged away by lots of nice documentation — those are `critical` checks.
- **Honest about judgment.** Things only a human/model can judge (clarity, design
  quality) are `llm_rubric` checks at modest weight, never silently counted as passes.

## Authoring a suite

See `schema/benchmark-suite.schema.yaml` for the full grammar and
`suites/security/security-auditor.benchmark.yaml` for a worked example. Then:

```bash
python -m benchmarks.framework.cli lint-suites --strict
```
