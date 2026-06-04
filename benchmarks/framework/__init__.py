"""Agent Blueprints benchmark framework.

A two-layer evaluation harness for OAT agent templates:

* Layer 1 - static validation (`static_validator`): scores a template definition on
  schema correctness, registry consistency, prompt rigor and success-condition quality.
  Runs anywhere, no agent execution required.

* Layer 2 - scenario scoring (`scorer`): grades the *output workspace* produced by an
  agent run against a declarative, domain-specific rubric of weighted checks.

Both layers emit the same `Scorecard` structure so results can be aggregated and
reported uniformly. See `benchmarks/README.md` for the scoring methodology.
"""

from .models import (
    CheckResult,
    Finding,
    Scenario,
    Scorecard,
    SuiteResult,
    BenchmarkSuite,
)

__all__ = [
    "CheckResult",
    "Finding",
    "Scenario",
    "Scorecard",
    "SuiteResult",
    "BenchmarkSuite",
]

__version__ = "1.0.0"
