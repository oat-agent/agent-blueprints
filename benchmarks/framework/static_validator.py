"""Layer 1 - static template validation and scoring.

Validates an OAT `AgentTemplate` definition against the schema and a set of quality
heuristics, producing a 0-100 `Scorecard` with findings. Also validates repo-wide
invariants: registry <-> filesystem consistency and benchmark-suite coverage.

This layer runs without executing any agent, so it is cheap enough to gate every PR.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .models import Finding, Scorecard, SEVERITY_WEIGHT, grade_for

# These mirror internal/factory/validator.go and types.go on the OAT
# `feature/agent-factory` branch. A template that violates a factory-fatal rule is
# rejected by AgentFactory.Validate()/CreateAgent and is therefore unusable, so we
# score those as `critical`/`major` rather than mere style nits.
ALLOWED_BASE_TYPES = {"worker", "review", "persistent"}
ALLOWED_PR_CREATION = {"required", "optional", "none"}
MECHANICAL_CONDITIONS = {
    "file_exists", "directory_exists", "dir_exists",
    "file_pattern_exists", "command_success",
}
ALLOWED_STABILITY = {"stable", "beta", "experimental"}
# Factory: isValidName -> ^[a-z0-9-]+$
NAME_RE = re.compile(r"^[a-z0-9-]+$")
# Factory: isValidVersion -> ^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$ (no +build metadata)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$")
# Factory: isValidVersionConstraint
VERSION_CONSTRAINT_RE = re.compile(r"^(>=?|<=?|~>|=)?\s*\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$")
# Factory: isValidMemory -> ^\d+(\.\d+)?[KMG]i?$
MEMORY_RE = re.compile(r"^\d+(\.\d+)?[KMG]i?$")
TEMPLATE_VAR_RE = re.compile(r"\{([a-z][a-z0-9_]*)\}")

# Penalty applied per finding = SEVERITY_WEIGHT * PENALTY_SCALE, subtracted from 100.
PENALTY_SCALE = 2.5


def _add(findings: List[Finding], rule: str, severity: str, message: str, location: Optional[str] = None) -> None:
    findings.append(Finding(rule=rule, severity=severity, message=message, location=location))


def _get(d: Any, *path: str) -> Tuple[bool, Any]:
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return False, None
        cur = cur[key]
    return True, cur


def validate_template(path: Path) -> Scorecard:
    """Validate a single template file and return its scorecard."""
    findings: List[Finding] = []
    category = path.parent.name
    stem = path.stem

    raw = path.read_text()
    try:
        doc = yaml.safe_load(raw)
    except Exception as e:
        _add(findings, "yaml.parse", "critical", f"YAML failed to parse: {e}")
        return _finalize(stem, category, findings)

    if not isinstance(doc, dict):
        _add(findings, "yaml.root", "critical", "Top-level document is not a mapping")
        return _finalize(stem, category, findings)

    # ---- top-level identity -------------------------------------------------
    if doc.get("apiVersion") != "agents.oat.dev/v1":
        _add(findings, "apiVersion", "major", f"Unexpected apiVersion {doc.get('apiVersion')!r}")
    if doc.get("kind") != "AgentTemplate":
        _add(findings, "kind", "major", f"Unexpected kind {doc.get('kind')!r}")

    # ---- metadata -----------------------------------------------------------
    md_ok, md = _get(doc, "metadata")
    name = None
    if not md_ok or not isinstance(md, dict):
        _add(findings, "metadata", "critical", "Missing metadata block")
    else:
        name = md.get("name")
        if not name:
            _add(findings, "metadata.name", "critical", "Missing metadata.name (factory rejects)")
        else:
            if not NAME_RE.match(str(name)):
                _add(findings, "metadata.name", "critical",
                     f"metadata.name {name!r} must be lowercase alphanumeric + hyphens (factory rejects)")
            if name != stem:
                _add(findings, "metadata.name", "major",
                     f"metadata.name {name!r} != filename {stem!r}")
        version = md.get("version")
        if not version:
            _add(findings, "metadata.version", "critical", "Missing metadata.version (factory rejects)")
        elif not SEMVER_RE.match(str(version)):
            _add(findings, "metadata.version", "major",
                 f"version {version!r} not factory-valid semver (\\d+.\\d+.\\d+[-prerelease])")
        # author + description are hard-required by the factory MetadataRule.
        if not md.get("author"):
            _add(findings, "metadata.author", "major", "Missing metadata.author (factory rejects)")
        desc = md.get("description")
        if not desc:
            _add(findings, "metadata.description", "major", "Missing metadata.description (factory rejects)")
        elif len(str(desc).strip()) < 40:
            _add(findings, "metadata.description", "minor", "Description too short (<40 chars)")
        tags = md.get("tags")
        if not tags or not isinstance(tags, list) or len(tags) < 2:
            _add(findings, "metadata.tags", "minor", "Provide at least 2 descriptive tags")

    # ---- spec.base ----------------------------------------------------------
    base_ok, base = _get(doc, "spec", "base")
    if not base_ok or not isinstance(base, dict):
        _add(findings, "spec.base", "critical", "Missing spec.base")
    else:
        btype = base.get("type")
        if not btype:
            _add(findings, "spec.base.type", "critical", "Missing spec.base.type (factory rejects)")
        elif btype not in ALLOWED_BASE_TYPES:
            _add(findings, "spec.base.type", "critical",
                 f"base.type {btype!r} not in {sorted(ALLOWED_BASE_TYPES)} (factory rejects)")
        if not base.get("model"):
            _add(findings, "spec.base.model", "minor", "Missing spec.base.model")
        temp = base.get("temperature")
        if temp is not None and not (isinstance(temp, (int, float)) and 0.0 <= temp <= 1.0):
            _add(findings, "spec.base.temperature", "major", f"temperature {temp!r} outside [0,1] (factory rejects)")

    # ---- spec.capabilities --------------------------------------------------
    cap_ok, cap = _get(doc, "spec", "capabilities")
    if not cap_ok or not isinstance(cap, dict):
        _add(findings, "spec.capabilities", "major", "Missing spec.capabilities")
    else:
        tools = cap.get("tools")
        if tools is None:
            _add(findings, "spec.capabilities.tools", "minor", "No tools declared")
        elif isinstance(tools, list):
            for i, t in enumerate(tools):
                if isinstance(t, dict):
                    tname = t.get("name", "")
                    if not tname:
                        _add(findings, "spec.capabilities.tools", "major", f"tool[{i}] missing name (factory rejects)")
                    elif tname.endswith('"') or tname.startswith('"'):
                        _add(findings, "spec.capabilities.tools", "major",
                             f"tool name {tname!r} has a stray quote (breaks version constraint parsing)")
                    ver = t.get("version")
                    if ver is None:
                        _add(findings, "spec.capabilities.tools", "info", f"tool {tname!r} has no version pin")
                    elif not VERSION_CONSTRAINT_RE.match(str(ver)):
                        _add(findings, "spec.capabilities.tools", "major",
                             f"tool {tname!r} version constraint {ver!r} is invalid (factory rejects)")
        apis = cap.get("apis")
        if isinstance(apis, list) and any(not a for a in apis):
            _add(findings, "spec.capabilities.apis", "major", "Empty API name (factory rejects)")

    # ---- spec.prompt --------------------------------------------------------
    pr_ok, prompt = _get(doc, "spec", "prompt")
    if not pr_ok or not isinstance(prompt, dict):
        _add(findings, "spec.prompt", "critical", "Missing spec.prompt")
    else:
        system = prompt.get("system") or ""
        slen = len(system.strip())
        if slen == 0:
            _add(findings, "spec.prompt.system", "critical", "Empty system prompt")
        elif slen < 200:
            _add(findings, "spec.prompt.system", "major", f"System prompt very short ({slen} chars)")
        elif slen < 400:
            _add(findings, "spec.prompt.system", "minor", f"System prompt short ({slen} chars)")
        low = system.lower()
        if "output" not in low:
            _add(findings, "spec.prompt.system", "minor", "System prompt does not describe output requirements")
        if not any(w in low for w in ("process", "steps", "1.", "procedure", "workflow")):
            _add(findings, "spec.prompt.system", "minor", "System prompt does not describe a process")

        tt = prompt.get("task_template") or ""
        tvars = set(TEMPLATE_VAR_RE.findall(tt))
        if not tt.strip():
            _add(findings, "spec.prompt.task_template", "minor", "Missing task_template")
        else:
            # Factory PromptRule: task_template must contain the "{task" placeholder.
            if "{task" not in tt:
                _add(findings, "spec.prompt.task_template", "major",
                     "task_template must contain a {task...} placeholder (factory rejects)")
            if not tvars:
                _add(findings, "spec.prompt.task_template", "minor", "task_template has no {variables}")

    # ---- spec.resources (optional, but if present must be factory-valid) ----
    res_ok, resources = _get(doc, "spec", "resources")
    if res_ok and isinstance(resources, dict):
        mem = resources.get("memory")
        if mem is not None and not MEMORY_RE.match(str(mem)):
            _add(findings, "spec.resources.memory", "major",
                 f"memory {mem!r} not in factory format (e.g. 2Gi, 512Mi) (factory rejects)")
        cpu = resources.get("cpu")
        if cpu is not None and isinstance(cpu, (int, float)) and cpu < 0:
            _add(findings, "spec.resources.cpu", "major", "cpu must be positive (factory rejects)")

    # ---- spec.behavior ------------------------------------------------------
    beh_ok, behavior = _get(doc, "spec", "behavior")
    if beh_ok and isinstance(behavior, dict):
        prc = behavior.get("pr_creation")
        if prc is not None and prc not in ALLOWED_PR_CREATION:
            _add(findings, "spec.behavior.pr_creation", "major",
                 f"pr_creation {prc!r} not in {sorted(ALLOWED_PR_CREATION)} (factory rejects)")

    # ---- spec.success -------------------------------------------------------
    su_ok, success = _get(doc, "spec", "success")
    if not su_ok or not isinstance(success, dict):
        _add(findings, "spec.success", "major", "Missing spec.success")
    else:
        conds = success.get("conditions")
        if not conds or not isinstance(conds, list):
            _add(findings, "spec.success.conditions", "major", "No success conditions defined")
        else:
            types = [c.get("type") for c in conds if isinstance(c, dict)]
            if not any(t in MECHANICAL_CONDITIONS for t in types):
                _add(findings, "spec.success.conditions", "major",
                     "No machine-verifiable condition (file/dir/command). "
                     "Success cannot be confirmed automatically.")
            semantic = [t for t in types if t not in MECHANICAL_CONDITIONS]
            if semantic:
                _add(findings, "spec.success.conditions", "info",
                     f"Semantic conditions need a benchmark suite to verify: {sorted(set(semantic))}")

    return _finalize(name or stem, category, findings)


def _finalize(name: str, category: str, findings: List[Finding]) -> Scorecard:
    penalty = sum(SEVERITY_WEIGHT.get(f.severity, 0.0) * PENALTY_SCALE for f in findings)
    score = max(0.0, 100.0 - penalty)
    return Scorecard(agent=name, category=category, score=score, grade=grade_for(score), findings=findings)


def validate_registry(repo_root: Path) -> List[Finding]:
    """Check registry.yaml <-> filesystem consistency."""
    findings: List[Finding] = []
    reg_path = repo_root / "registry.yaml"
    if not reg_path.is_file():
        return [Finding("registry.missing", "critical", "registry.yaml not found")]
    reg = yaml.safe_load(reg_path.read_text()) or {}
    entries = reg.get("templates", []) or []

    declared_paths = set()
    declared_names = set()
    for e in entries:
        p = e.get("path")
        n = e.get("name")
        declared_names.add(n)
        if p:
            declared_paths.add(p)
            if not (repo_root / p).is_file():
                # FetchFromRegistry loads every entry and aborts on the first
                # failure, so one missing file makes the WHOLE registry unloadable.
                _add(findings, "registry.missing_file", "critical",
                     f"registry references {p} but file is absent — this breaks "
                     f"FetchFromRegistry for the entire repo", location="registry.yaml")
            elif n and Path(p).stem != n:
                _add(findings, "registry.name_mismatch", "minor",
                     f"registry name {n!r} != filename {Path(p).stem!r}", location=p)
        stab = e.get("stability")
        if stab is not None and stab not in ALLOWED_STABILITY:
            _add(findings, "registry.stability", "minor",
                 f"{n}: invalid stability {stab!r}", location="registry.yaml")

    for f in (repo_root / "templates").glob("*/*.yaml"):
        rel = str(f.relative_to(repo_root))
        if rel not in declared_paths:
            _add(findings, "registry.orphan_file", "major",
                 f"template {rel} is not listed in registry.yaml", location=rel)
    return findings


def validate_suite_coverage(repo_root: Path) -> List[Finding]:
    """Every template should have a matching benchmark suite."""
    findings: List[Finding] = []
    suites_dir = repo_root / "benchmarks" / "suites"
    suite_agents = set()
    if suites_dir.is_dir():
        for sf in suites_dir.glob("**/*.benchmark.yaml"):
            try:
                d = yaml.safe_load(sf.read_text()) or {}
                if d.get("agent"):
                    suite_agents.add(d["agent"])
            except Exception:
                _add(findings, "suite.parse", "minor", f"could not parse suite {sf}")
    for f in (repo_root / "templates").glob("*/*.yaml"):
        if f.stem not in suite_agents:
            _add(findings, "suite.missing", "minor",
                 f"no benchmark suite for template {f.stem}", location=str(f.relative_to(repo_root)))
    return findings
