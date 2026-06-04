"""Layer 2 - behavioral scenario scoring.

Given a benchmark suite and a directory containing the artifacts an agent produced
for each scenario, compute weighted scores with critical-check gating.

Output-workspace layout expected by `score_suite`:

    <output_root>/<scenario_id>/   # everything the agent produced for that scenario

If a scenario directory is missing, the scenario scores 0 (the agent produced
nothing) rather than being skipped, so coverage gaps are visible.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .checks import CheckContext, run_check
from .models import (
    BenchmarkSuite,
    CheckResult,
    Scenario,
    ScenarioResult,
    SuiteResult,
)


def score_scenario(
    scenario: Scenario,
    workspace: Path,
    ctx: Optional[CheckContext] = None,
) -> ScenarioResult:
    """Evaluate every check in a scenario against ``workspace`` and aggregate.

    Scoring rule (see README): scenario score = sum(weight * check_score) over
    *non-skipped* checks / sum(weight). A failed `critical` check forces the
    scenario to fail and clamps the reported score to at most the pass threshold
    minus epsilon so it can never read as a pass.
    """
    if ctx is None:
        ctx = CheckContext(workspace=workspace)
    ctx.workspace = workspace

    results: list[CheckResult] = []
    weighted_sum = 0.0
    weight_total = 0.0
    critical_failure = False

    for chk in scenario.checks:
        outcome = run_check(chk.type, workspace, chk.params, ctx)
        cr = CheckResult(
            check_id=chk.id,
            type=chk.type,
            weight=chk.weight,
            passed=outcome.passed,
            critical=chk.critical,
            score=outcome.score,
            detail=outcome.detail,
            skipped=outcome.skipped,
            skip_reason=outcome.skip_reason,
        )
        results.append(cr)

        if outcome.skipped:
            continue
        weighted_sum += chk.weight * outcome.score
        weight_total += chk.weight
        if chk.critical and not outcome.passed:
            critical_failure = True

    score = (weighted_sum / weight_total) if weight_total > 0 else 0.0
    passed = (score >= scenario.pass_threshold) and not critical_failure
    if critical_failure:
        # Make sure a critical failure never reads as a pass.
        score = min(score, max(0.0, scenario.pass_threshold - 1e-9))

    return ScenarioResult(
        scenario_id=scenario.id,
        score=score,
        passed=passed,
        critical_failure=critical_failure,
        checks=results,
    )


def score_suite(
    suite: BenchmarkSuite,
    output_root: Path,
    ctx: Optional[CheckContext] = None,
) -> SuiteResult:
    """Score every scenario in a suite. Suite score = mean of scenario scores."""
    scenario_results: list[ScenarioResult] = []
    for scenario in suite.scenarios:
        ws = output_root / scenario.id
        if not ws.is_dir():
            scenario_results.append(
                ScenarioResult(
                    scenario_id=scenario.id,
                    score=0.0,
                    passed=False,
                    critical_failure=True,
                    checks=[
                        CheckResult(
                            check_id="__workspace__",
                            type="dir_exists",
                            weight=1.0,
                            passed=False,
                            critical=True,
                            detail=f"no output dir for scenario at {ws}",
                        )
                    ],
                )
            )
            continue
        scenario_results.append(score_scenario(scenario, ws, ctx))

    if scenario_results:
        suite_score = sum(s.score for s in scenario_results) / len(scenario_results)
        passed = all(s.passed for s in scenario_results)
    else:
        suite_score, passed = 0.0, False

    return SuiteResult(
        agent=suite.agent,
        category=suite.category,
        score=suite_score,
        passed=passed,
        scenarios=scenario_results,
    )
