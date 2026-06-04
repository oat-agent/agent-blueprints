"""Check implementations for the scenario scorer.

A check is a deterministic (or pluggable-judge) predicate evaluated against the
*output workspace* an agent produced. Each check returns a `CheckOutcome`.

All checks are registered in `CHECK_REGISTRY` keyed by their `type`. Adding a new
check type is a matter of writing a function and decorating it with `@check`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - yaml is a declared dependency
    yaml = None


@dataclass
class CheckOutcome:
    passed: bool
    score: float = 0.0
    detail: str = ""
    skipped: bool = False
    skip_reason: str = ""


CheckFn = Callable[[Path, Dict[str, Any], "CheckContext"], CheckOutcome]
CHECK_REGISTRY: Dict[str, CheckFn] = {}


@dataclass
class CheckContext:
    """Runtime context handed to every check.

    `judge` is an optional callable implementing LLM-as-judge scoring. When absent,
    `llm_rubric` checks are *skipped* rather than failed, so deterministic suites
    stay reproducible in CI while richer grading can be layered on locally.
    """

    workspace: Path
    judge: Optional[Callable[[str, Dict[str, Any], Path], CheckOutcome]] = None
    command_timeout: int = 120
    allow_commands: bool = True


def check(type_name: str) -> Callable[[CheckFn], CheckFn]:
    def deco(fn: CheckFn) -> CheckFn:
        CHECK_REGISTRY[type_name] = fn
        return fn

    return deco


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

_OPS: Dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "contains": lambda a, b: b in a,
}


def _resolve(workspace: Path, rel: str) -> Path:
    """Resolve a path inside the workspace, blocking escapes via ``..``."""
    target = (workspace / rel).resolve()
    ws = workspace.resolve()
    if ws not in target.parents and target != ws:
        raise ValueError(f"path {rel!r} escapes the workspace sandbox")
    return target


def _dotted_get(data: Any, query: str) -> Tuple[bool, Any]:
    """Look up ``a.b[0].c`` style paths. Returns (found, value)."""
    token_re = re.compile(r"([^.\[\]]+)|\[(\d+)\]")
    cur = data
    for key, idx in token_re.findall(query):
        try:
            if idx != "":
                cur = cur[int(idx)]
            else:
                if isinstance(cur, dict):
                    cur = cur[key]
                else:
                    return False, None
        except (KeyError, IndexError, TypeError):
            return False, None
    return True, cur


# Common credential / secret patterns used by `no_secrets`.
_SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",                       # AWS access key id
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"ghp_[A-Za-z0-9]{36}",                    # GitHub PAT
    r"xox[baprs]-[A-Za-z0-9-]{10,}",           # Slack token
    r"AIza[0-9A-Za-z\-_]{35}",                 # Google API key
    r"(?i)aws_secret_access_key\s*[=:]\s*[A-Za-z0-9/+]{40}",
]


# --------------------------------------------------------------------------- #
# Filesystem checks
# --------------------------------------------------------------------------- #

@check("file_exists")
def _file_exists(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    path = _resolve(ws, p["path"])
    ok = path.is_file()
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"{p['path']} {'found' if ok else 'missing'}")


@check("dir_exists")
def _dir_exists(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    path = _resolve(ws, p["path"])
    ok = path.is_dir()
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"{p['path']}/ {'found' if ok else 'missing'}")


@check("file_glob")
def _file_glob(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    min_matches = int(p.get("min_matches", 1))
    matches = list(ws.glob(p["pattern"]))
    ok = len(matches) >= min_matches
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"{len(matches)} match(es) for {p['pattern']!r} (need {min_matches})")


@check("file_contains")
def _file_contains(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    path = _resolve(ws, p["path"])
    if not path.is_file():
        return CheckOutcome(False, 0.0, f"{p['path']} missing")
    flags = re.IGNORECASE if p.get("ignore_case") else 0
    text = path.read_text(errors="replace")
    count = len(re.findall(p["pattern"], text, flags))
    min_count = int(p.get("min_count", 1))
    ok = count >= min_count
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"pattern matched {count}x (need {min_count}) in {p['path']}")


@check("file_not_contains")
def _file_not_contains(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    path = _resolve(ws, p["path"])
    if not path.is_file():
        # Nothing to leak if file is absent; treat as pass.
        return CheckOutcome(True, 1.0, f"{p['path']} absent")
    flags = re.IGNORECASE if p.get("ignore_case") else 0
    text = path.read_text(errors="replace")
    found = re.search(p["pattern"], text, flags)
    ok = found is None
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"forbidden pattern {'absent' if ok else 'PRESENT'} in {p['path']}")


@check("no_secrets")
def _no_secrets(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    globs = p.get("globs", ["**/*.md", "**/*.json", "**/*.txt", "**/*.yaml", "**/*.yml"])
    patterns = [re.compile(pat) for pat in _SECRET_PATTERNS + list(p.get("extra_patterns", []))]
    offenders = []
    for g in globs:
        for f in ws.glob(g):
            if not f.is_file():
                continue
            try:
                text = f.read_text(errors="replace")
            except Exception:
                continue
            for pat in patterns:
                if pat.search(text):
                    offenders.append(str(f.relative_to(ws)))
                    break
    ok = not offenders
    return CheckOutcome(ok, 1.0 if ok else 0.0, "no secrets found" if ok else f"secrets in: {', '.join(offenders[:5])}")


# --------------------------------------------------------------------------- #
# Structured-data checks
# --------------------------------------------------------------------------- #

@check("json_valid")
def _json_valid(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    path = _resolve(ws, p["path"])
    if not path.is_file():
        return CheckOutcome(False, 0.0, f"{p['path']} missing")
    try:
        json.loads(path.read_text())
        return CheckOutcome(True, 1.0, f"{p['path']} is valid JSON")
    except Exception as e:
        return CheckOutcome(False, 0.0, f"{p['path']} invalid JSON: {e}")


@check("yaml_valid")
def _yaml_valid(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    if yaml is None:
        return CheckOutcome(False, 0.0, "pyyaml not installed", skipped=True, skip_reason="pyyaml missing")
    path = _resolve(ws, p["path"])
    if not path.is_file():
        return CheckOutcome(False, 0.0, f"{p['path']} missing")
    try:
        list(yaml.safe_load_all(path.read_text()))
        return CheckOutcome(True, 1.0, f"{p['path']} is valid YAML")
    except Exception as e:
        return CheckOutcome(False, 0.0, f"{p['path']} invalid YAML: {e}")


@check("json_path")
def _json_path(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    path = _resolve(ws, p["path"])
    if not path.is_file():
        return CheckOutcome(False, 0.0, f"{p['path']} missing")
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return CheckOutcome(False, 0.0, f"{p['path']} invalid JSON: {e}")
    found, value = _dotted_get(data, p["query"])
    op = p.get("op", "exists")
    if op == "exists":
        return CheckOutcome(found, 1.0 if found else 0.0, f"{p['query']} {'exists' if found else 'absent'}")
    if not found:
        return CheckOutcome(False, 0.0, f"{p['query']} absent")
    if op not in _OPS:
        return CheckOutcome(False, 0.0, f"unknown op {op!r}")
    ok = bool(_OPS[op](value, p.get("value")))
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"{p['query']}={value!r} {op} {p.get('value')!r} -> {ok}")


@check("metric_threshold")
def _metric_threshold(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    """Read a numeric metric the agent reported and compare against a threshold."""
    path = _resolve(ws, p["path"])
    if not path.is_file():
        return CheckOutcome(False, 0.0, f"{p['path']} missing")
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return CheckOutcome(False, 0.0, f"{p['path']} invalid JSON: {e}")
    found, value = _dotted_get(data, p["key"])
    if not found:
        return CheckOutcome(False, 0.0, f"metric {p['key']} absent")
    try:
        value = float(value)
    except (TypeError, ValueError):
        return CheckOutcome(False, 0.0, f"metric {p['key']}={value!r} not numeric")
    op = p.get("op", "gte")
    threshold = float(p["value"])
    ok = bool(_OPS[op](value, threshold))
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"{p['key']}={value} {op} {threshold} -> {ok}")


# --------------------------------------------------------------------------- #
# Command checks
# --------------------------------------------------------------------------- #

def _run(ws: Path, p: Dict[str, Any], ctx: CheckContext):
    cwd = ws
    if p.get("cwd"):
        cwd = _resolve(ws, p["cwd"])
    timeout = int(p.get("timeout", ctx.command_timeout))
    return subprocess.run(
        p["command"],
        shell=True,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "CI": "1"},
    )


@check("command_success")
def _command_success(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    if not ctx.allow_commands:
        return CheckOutcome(False, 0.0, "commands disabled", skipped=True, skip_reason="commands disabled")
    try:
        proc = _run(ws, p, ctx)
    except subprocess.TimeoutExpired:
        return CheckOutcome(False, 0.0, f"command timed out: {p['command']}")
    except FileNotFoundError as e:
        return CheckOutcome(False, 0.0, f"command unavailable: {e}", skipped=True, skip_reason="binary missing")
    ok = proc.returncode == 0
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"exit={proc.returncode}: {p['command']}")


@check("command_output_matches")
def _command_output_matches(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    if not ctx.allow_commands:
        return CheckOutcome(False, 0.0, "commands disabled", skipped=True, skip_reason="commands disabled")
    try:
        proc = _run(ws, p, ctx)
    except subprocess.TimeoutExpired:
        return CheckOutcome(False, 0.0, f"command timed out: {p['command']}")
    except FileNotFoundError as e:
        return CheckOutcome(False, 0.0, f"command unavailable: {e}", skipped=True, skip_reason="binary missing")
    out = proc.stdout + proc.stderr
    ok = re.search(p["pattern"], out) is not None
    return CheckOutcome(ok, 1.0 if ok else 0.0, f"output {'matched' if ok else 'did not match'} {p['pattern']!r}")


# --------------------------------------------------------------------------- #
# LLM-as-judge (pluggable)
# --------------------------------------------------------------------------- #

@check("llm_rubric")
def _llm_rubric(ws: Path, p: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    """Graded qualitative check. Skipped unless a judge is wired into the context.

    Suites keep `llm_rubric` checks at modest weight so a run stays meaningful even
    when no judge is configured (CI / offline), while still recording where human or
    model judgment is expected.
    """
    if ctx.judge is None:
        return CheckOutcome(
            False, 0.0, "no judge configured",
            skipped=True, skip_reason="llm judge not configured",
        )
    return ctx.judge(p.get("criteria", p.get("description", "")), p, ws)


def run_check(check_type: str, ws: Path, params: Dict[str, Any], ctx: CheckContext) -> CheckOutcome:
    fn = CHECK_REGISTRY.get(check_type)
    if fn is None:
        return CheckOutcome(False, 0.0, f"unknown check type {check_type!r}")
    try:
        return fn(ws, params, ctx)
    except KeyError as e:
        return CheckOutcome(False, 0.0, f"missing required param {e} for {check_type}")
    except Exception as e:  # defensive: a broken check should fail, not crash the run
        return CheckOutcome(False, 0.0, f"{check_type} error: {e}")
