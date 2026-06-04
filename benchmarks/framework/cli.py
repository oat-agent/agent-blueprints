"""Command-line entrypoint for the benchmark framework.

Examples
--------
Static validation of every template (Layer 1)::

    python -m benchmarks.framework.cli validate

    # fail the process if any template scores below 80 or has major findings
    python -m benchmarks.framework.cli validate --min-score 80 --fail-on major

Behavioral scoring of an agent's outputs against one suite (Layer 2)::

    python -m benchmarks.framework.cli score \
        --suite benchmarks/suites/security/security-auditor.benchmark.yaml \
        --outputs runs/security-auditor/

Lint the benchmark suites themselves::

    python -m benchmarks.framework.cli lint-suites
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import report
from .checks import CheckContext
from .loader import find_repo_root, load_suites, load_templates
from .models import BenchmarkSuite
from .scorer import score_suite
from .static_validator import (
    validate_registry,
    validate_suite_coverage,
    validate_template,
)

import yaml

SEVERITY_RANK = {"info": 0, "minor": 1, "major": 2, "critical": 3}


def cmd_validate(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    templates = load_templates(repo_root)
    scorecards = [validate_template(t) for t in templates]
    registry_findings = validate_registry(repo_root)
    coverage_findings = validate_suite_coverage(repo_root)

    if args.format == "json":
        print(report.static_report_json(scorecards, registry_findings, coverage_findings))
    else:
        print(report.static_report_markdown(scorecards, registry_findings, coverage_findings))

    if args.out:
        Path(args.out).write_text(
            report.static_report_json(scorecards, registry_findings, coverage_findings)
        )

    # Exit-code policy for CI gating.
    failed = False
    threshold = SEVERITY_RANK.get(args.fail_on, 99) if args.fail_on else 99
    for s in scorecards:
        if args.min_score and s.score < args.min_score:
            failed = True
        if any(SEVERITY_RANK.get(f.severity, 0) >= threshold for f in s.findings):
            failed = True
    if args.fail_on:
        if any(SEVERITY_RANK.get(f.severity, 0) >= threshold for f in registry_findings):
            failed = True
    return 1 if failed else 0


def cmd_score(args: argparse.Namespace) -> int:
    suite_data = yaml.safe_load(Path(args.suite).read_text())
    suite = BenchmarkSuite.from_dict(suite_data, source_path=args.suite)
    ctx = CheckContext(
        workspace=Path(args.outputs),
        allow_commands=not args.no_commands,
    )
    result = score_suite(suite, Path(args.outputs), ctx)
    print(report.behavioral_report_json([result]) if args.format == "json"
          else report.behavioral_report_markdown([result]))
    return 0 if result.passed else 1


def cmd_lint_suites(args: argparse.Namespace) -> int:
    """Validate that suites are well-formed and target existing templates."""
    repo_root = find_repo_root()
    suites = load_suites(repo_root)
    template_names = {t.stem for t in load_templates(repo_root)}
    problems = 0
    for suite in suites:
        if suite.agent not in template_names:
            print(f"[warn] suite {suite.source_path}: agent {suite.agent!r} has no template")
            problems += 1
        if not suite.scenarios:
            print(f"[warn] suite {suite.source_path}: no scenarios")
            problems += 1
        seen = set()
        for sc in suite.scenarios:
            if sc.id in seen:
                print(f"[warn] suite {suite.agent}: duplicate scenario id {sc.id!r}")
                problems += 1
            seen.add(sc.id)
            if not sc.checks:
                print(f"[warn] suite {suite.agent}/{sc.id}: no checks")
                problems += 1
            wtotal = sum(c.weight for c in sc.checks)
            if wtotal <= 0:
                print(f"[warn] suite {suite.agent}/{sc.id}: total weight is 0")
                problems += 1
    print(f"\nLinted {len(suites)} suites, {problems} problem(s).")
    return 1 if problems and args.strict else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent-benchmark", description="OAT agent template benchmark")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="static validation of all templates (Layer 1)")
    v.add_argument("--format", choices=["markdown", "json"], default="markdown")
    v.add_argument("--out", help="also write the JSON report to this path")
    v.add_argument("--min-score", type=float, default=0.0, help="fail if any template scores below this")
    v.add_argument("--fail-on", choices=["minor", "major", "critical"], help="fail on findings at/above this severity")
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("score", help="score an agent's outputs against a suite (Layer 2)")
    s.add_argument("--suite", required=True, help="path to a *.benchmark.yaml suite")
    s.add_argument("--outputs", required=True, help="root dir containing <scenario_id>/ output dirs")
    s.add_argument("--format", choices=["markdown", "json"], default="markdown")
    s.add_argument("--no-commands", action="store_true", help="skip command_* checks (sandbox)")
    s.set_defaults(func=cmd_score)

    ls = sub.add_parser("lint-suites", help="validate suite files are well-formed")
    ls.add_argument("--strict", action="store_true", help="non-zero exit on any problem")
    ls.set_defaults(func=cmd_lint_suites)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
