"""Loading helpers for templates and benchmark suites."""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from .models import BenchmarkSuite


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upward to find the repo root (the dir containing registry.yaml)."""
    cur = (start or Path(__file__)).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "registry.yaml").is_file():
            return parent
    raise FileNotFoundError("could not locate repo root (registry.yaml)")


def load_templates(repo_root: Path) -> List[Path]:
    return sorted((repo_root / "templates").glob("*/*.yaml"))


def load_suites(repo_root: Path) -> List[BenchmarkSuite]:
    suites: List[BenchmarkSuite] = []
    suites_dir = repo_root / "benchmarks" / "suites"
    if not suites_dir.is_dir():
        return suites
    for sf in sorted(suites_dir.glob("**/*.benchmark.yaml")):
        data = yaml.safe_load(sf.read_text())
        if data:
            suites.append(BenchmarkSuite.from_dict(data, source_path=str(sf)))
    return suites
