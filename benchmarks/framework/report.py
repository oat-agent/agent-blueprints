"""Render benchmark results as JSON and Markdown."""

from __future__ import annotations

import json
from typing import Dict, List

from .models import Finding, Scorecard, SuiteResult


def static_report_json(scorecards: List[Scorecard], registry_findings: List[Finding],
                       coverage_findings: List[Finding]) -> str:
    overall = (sum(s.score for s in scorecards) / len(scorecards)) if scorecards else 0.0
    payload = {
        "summary": {
            "templates_evaluated": len(scorecards),
            "average_score": round(overall, 2),
            "registry_findings": len(registry_findings),
            "coverage_findings": len(coverage_findings),
        },
        "templates": [s.to_dict() for s in scorecards],
        "registry": [f.to_dict() for f in registry_findings],
        "coverage": [f.to_dict() for f in coverage_findings],
    }
    return json.dumps(payload, indent=2)


def static_report_markdown(scorecards: List[Scorecard], registry_findings: List[Finding],
                           coverage_findings: List[Finding]) -> str:
    lines: List[str] = []
    overall = (sum(s.score for s in scorecards) / len(scorecards)) if scorecards else 0.0
    lines.append("# Static Validation Scorecard\n")
    lines.append(f"**Templates evaluated:** {len(scorecards)}  ")
    lines.append(f"**Average score:** {overall:.1f}/100  ")
    lines.append(f"**Registry findings:** {len(registry_findings)}  ")
    lines.append(f"**Coverage findings:** {len(coverage_findings)}\n")

    by_cat: Dict[str, List[Scorecard]] = {}
    for s in scorecards:
        by_cat.setdefault(s.category, []).append(s)

    lines.append("## Scores by template\n")
    lines.append("| Category | Agent | Score | Grade | Findings |")
    lines.append("|---|---|---:|:--:|---:|")
    for cat in sorted(by_cat):
        for s in sorted(by_cat[cat], key=lambda x: x.agent):
            crit = sum(1 for f in s.findings if f.severity in ("major", "critical"))
            lines.append(f"| {cat} | {s.agent} | {s.score:.0f} | {s.grade} | {len(s.findings)} ({crit} major+) |")

    flagged = [s for s in scorecards if any(f.severity in ("major", "critical") for f in s.findings)]
    if flagged:
        lines.append("\n## Templates with major/critical findings\n")
        for s in sorted(flagged, key=lambda x: x.score):
            lines.append(f"### {s.category}/{s.agent} — {s.score:.0f} ({s.grade})")
            for f in s.findings:
                if f.severity in ("major", "critical"):
                    loc = f" ({f.location})" if f.location else ""
                    lines.append(f"- **{f.severity.upper()}** `{f.rule}`: {f.message}{loc}")
            lines.append("")

    if registry_findings:
        lines.append("## Registry consistency\n")
        for f in registry_findings:
            loc = f" ({f.location})" if f.location else ""
            lines.append(f"- **{f.severity.upper()}** `{f.rule}`: {f.message}{loc}")
        lines.append("")

    if coverage_findings:
        lines.append("## Benchmark-suite coverage gaps\n")
        for f in coverage_findings:
            lines.append(f"- `{f.rule}`: {f.message}")
        lines.append("")

    return "\n".join(lines)


def behavioral_report_json(results: List[SuiteResult]) -> str:
    overall = (sum(r.score for r in results) / len(results)) if results else 0.0
    payload = {
        "summary": {
            "suites_evaluated": len(results),
            "average_score": round(overall, 4),
            "passed": sum(1 for r in results if r.passed),
        },
        "suites": [r.to_dict() for r in results],
    }
    return json.dumps(payload, indent=2)


def behavioral_report_markdown(results: List[SuiteResult]) -> str:
    lines: List[str] = []
    overall = (sum(r.score for r in results) / len(results)) if results else 0.0
    lines.append("# Behavioral Benchmark Results\n")
    lines.append(f"**Suites evaluated:** {len(results)}  ")
    lines.append(f"**Average score:** {overall*100:.1f}%  ")
    lines.append(f"**Suites passed:** {sum(1 for r in results if r.passed)}/{len(results)}\n")
    lines.append("| Category | Agent | Score | Passed | Scenarios |")
    lines.append("|---|---|---:|:--:|---:|")
    for r in sorted(results, key=lambda x: (x.category, x.agent)):
        passed_n = sum(1 for s in r.scenarios if s.passed)
        lines.append(f"| {r.category} | {r.agent} | {r.score*100:.0f}% | "
                     f"{'PASS' if r.passed else 'FAIL'} | {passed_n}/{len(r.scenarios)} |")
    return "\n".join(lines)
