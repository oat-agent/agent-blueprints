"""Core data structures shared across the benchmark framework.

These are intentionally plain dataclasses with `to_dict()` helpers so scorecards
serialize cleanly to JSON without pulling in extra dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# Severity ordering used by the static validator. Higher = worse.
SEVERITY_WEIGHT = {
    "info": 0.0,
    "minor": 1.0,
    "major": 3.0,
    "critical": 8.0,
}


@dataclass
class Finding:
    """A single issue surfaced by the static validator."""

    rule: str
    severity: str  # info | minor | major | critical
    message: str
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    """Outcome of evaluating one rubric check against an agent output workspace."""

    check_id: str
    type: str
    weight: float
    passed: bool
    critical: bool = False
    score: float = 0.0  # 0..1; usually 0 or 1, fractional for graded checks
    detail: str = ""
    skipped: bool = False
    skip_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Check:
    """A declarative rubric check parsed from a benchmark suite YAML."""

    id: str
    type: str
    weight: float = 1.0
    critical: bool = False
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Check":
        known = {"id", "type", "weight", "critical", "description"}
        params = {k: v for k, v in data.items() if k not in known}
        return cls(
            id=data["id"],
            type=data["type"],
            weight=float(data.get("weight", 1.0)),
            critical=bool(data.get("critical", False)),
            description=data.get("description", ""),
            params=params,
        )


@dataclass
class Scenario:
    """One task scenario the agent must satisfy."""

    id: str
    description: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    workspace: Optional[str] = None  # fixture dir copied in as the starting repo
    pass_threshold: float = 0.7
    checks: List[Check] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        return cls(
            id=data["id"],
            description=data.get("description", ""),
            inputs=data.get("inputs", {}) or {},
            workspace=data.get("workspace"),
            pass_threshold=float(data.get("pass_threshold", 0.7)),
            checks=[Check.from_dict(c) for c in data.get("checks", [])],
        )


@dataclass
class BenchmarkSuite:
    """A per-agent benchmark suite: which template it targets + its scenarios."""

    agent: str
    category: str = ""
    description: str = ""
    template: str = ""  # path to the template this suite tests
    scenarios: List[Scenario] = field(default_factory=list)
    source_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_path: Optional[str] = None) -> "BenchmarkSuite":
        return cls(
            agent=data["agent"],
            category=data.get("category", ""),
            description=data.get("description", ""),
            template=data.get("template", ""),
            scenarios=[Scenario.from_dict(s) for s in data.get("scenarios", [])],
            source_path=source_path,
        )


@dataclass
class ScenarioResult:
    scenario_id: str
    score: float
    passed: bool
    critical_failure: bool
    checks: List[CheckResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "score": round(self.score, 4),
            "passed": self.passed,
            "critical_failure": self.critical_failure,
            "checks": [c.to_dict() for c in self.checks],
        }


@dataclass
class SuiteResult:
    """Aggregated behavioral result for one agent's benchmark suite."""

    agent: str
    category: str
    score: float
    passed: bool
    scenarios: List[ScenarioResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "category": self.category,
            "score": round(self.score, 4),
            "passed": self.passed,
            "scenarios": [s.to_dict() for s in self.scenarios],
        }


@dataclass
class Scorecard:
    """Static-validation scorecard for a single template."""

    agent: str
    category: str
    score: float  # 0..100
    grade: str
    findings: List[Finding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "category": self.category,
            "score": round(self.score, 2),
            "grade": self.grade,
            "findings": [f.to_dict() for f in self.findings],
        }


def grade_for(score_0_100: float) -> str:
    """Map a 0..100 score to a letter grade."""
    if score_0_100 >= 90:
        return "A"
    if score_0_100 >= 80:
        return "B"
    if score_0_100 >= 70:
        return "C"
    if score_0_100 >= 60:
        return "D"
    return "F"
