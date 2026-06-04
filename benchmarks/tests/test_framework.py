"""Unit tests for the benchmark framework. Run with: python -m unittest discover benchmarks/tests"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Make the repo root importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.framework.checks import CheckContext, run_check  # noqa: E402
from benchmarks.framework.models import Check, Scenario  # noqa: E402
from benchmarks.framework.scorer import score_scenario  # noqa: E402
from benchmarks.framework.static_validator import validate_template  # noqa: E402


GOOD_TEMPLATE = """\
apiVersion: agents.oat.dev/v1
kind: AgentTemplate
metadata:
  name: good-agent
  version: 1.0.0
  author: oat
  description: A perfectly reasonable agent that does a clearly described job well.
  tags: [a, b]
spec:
  base:
    type: worker
    model: claude-3-opus
    temperature: 0.1
  capabilities:
    tools:
      - name: git
        version: ">=2.0.0"
  prompt:
    system: |
      You are a helpful agent. Follow this process step by step.
      1. Do the thing.
      2. Verify the thing.
      Output requirements: write report.md describing what you did and why.
      Make sure the process is repeatable and the output is complete and correct.
    task_template: |
      Task: {task_description}
  success:
    conditions:
      - type: file_exists
        path: report.md
"""

BAD_TEMPLATE = """\
apiVersion: wrong/v9
kind: NotATemplate
metadata:
  name: mismatched-name
spec:
  base:
    type: dragon
  prompt:
    system: "too short"
  success:
    conditions:
      - type: test_coverage
        minimum: 80
"""


class ChecksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)
        self.ctx = CheckContext(workspace=self.ws)

    def tearDown(self):
        self.tmp.cleanup()

    def test_file_exists(self):
        (self.ws / "a.txt").write_text("hi")
        self.assertTrue(run_check("file_exists", self.ws, {"path": "a.txt"}, self.ctx).passed)
        self.assertFalse(run_check("file_exists", self.ws, {"path": "missing.txt"}, self.ctx).passed)

    def test_path_escape_blocked(self):
        out = run_check("file_exists", self.ws, {"path": "../../etc/passwd"}, self.ctx)
        self.assertFalse(out.passed)
        self.assertIn("escapes", out.detail)

    def test_file_contains_and_not_contains(self):
        (self.ws / "r.md").write_text("Critical: SQL injection found\nfix it")
        self.assertTrue(run_check("file_contains", self.ws, {"path": "r.md", "pattern": "SQL injection"}, self.ctx).passed)
        self.assertTrue(run_check("file_not_contains", self.ws, {"path": "r.md", "pattern": "AKIA"}, self.ctx).passed)

    def test_no_secrets(self):
        (self.ws / "leak.md").write_text("token AKIAIOSFODNN7EXAMPLE here")
        self.assertFalse(run_check("no_secrets", self.ws, {}, self.ctx).passed)
        (self.ws / "leak.md").write_text("nothing sensitive")
        self.assertTrue(run_check("no_secrets", self.ws, {}, self.ctx).passed)

    def test_json_path_and_metric(self):
        (self.ws / "m.json").write_text(json.dumps({"coverage": {"pct": 92}, "items": [1, 2, 3]}))
        self.assertTrue(run_check("json_path", self.ws, {"path": "m.json", "query": "items[2]", "op": "eq", "value": 3}, self.ctx).passed)
        self.assertTrue(run_check("metric_threshold", self.ws, {"path": "m.json", "key": "coverage.pct", "op": "gte", "value": 80}, self.ctx).passed)
        self.assertFalse(run_check("metric_threshold", self.ws, {"path": "m.json", "key": "coverage.pct", "op": "gte", "value": 99}, self.ctx).passed)

    def test_command_success(self):
        self.assertTrue(run_check("command_success", self.ws, {"command": "true"}, self.ctx).passed)
        self.assertFalse(run_check("command_success", self.ws, {"command": "false"}, self.ctx).passed)

    def test_llm_rubric_skipped_without_judge(self):
        out = run_check("llm_rubric", self.ws, {"criteria": "is it good?"}, self.ctx)
        self.assertTrue(out.skipped)


class ScenarioScoringTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_weighted_and_critical_gating(self):
        (self.ws / "report.md").write_text("done")
        scenario = Scenario(
            id="s1",
            pass_threshold=0.5,
            checks=[
                Check(id="has_report", type="file_exists", weight=1.0, critical=True, params={"path": "report.md"}),
                Check(id="has_extra", type="file_exists", weight=1.0, params={"path": "extra.md"}),
            ],
        )
        res = score_scenario(scenario, self.ws)
        self.assertAlmostEqual(res.score, 0.5, places=3)
        self.assertFalse(res.critical_failure)

        # Now make the critical check fail -> scenario must fail regardless of score.
        (self.ws / "report.md").unlink()
        (self.ws / "extra.md").write_text("x")
        res2 = score_scenario(scenario, self.ws)
        self.assertTrue(res2.critical_failure)
        self.assertFalse(res2.passed)

    def test_skipped_checks_excluded_from_denominator(self):
        (self.ws / "report.md").write_text("done")
        scenario = Scenario(
            id="s2",
            pass_threshold=0.9,
            checks=[
                Check(id="has_report", type="file_exists", weight=1.0, params={"path": "report.md"}),
                Check(id="judge", type="llm_rubric", weight=5.0, params={"criteria": "quality"}),
            ],
        )
        res = score_scenario(scenario, self.ws)
        # llm_rubric is skipped (no judge), so score should be 1.0 from the single real check.
        self.assertAlmostEqual(res.score, 1.0, places=3)
        self.assertTrue(res.passed)


class StaticValidatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "cat").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_good_template_scores_high(self):
        p = self.dir / "cat" / "good-agent.yaml"
        p.write_text(GOOD_TEMPLATE)
        card = validate_template(p)
        self.assertGreaterEqual(card.score, 95)
        self.assertEqual(card.grade, "A")

    def test_bad_template_scores_low_and_flags_critical(self):
        p = self.dir / "cat" / "mismatched-name.yaml"
        p.write_text(BAD_TEMPLATE)
        card = validate_template(p)
        self.assertLess(card.score, 70)
        sev = {f.severity for f in card.findings}
        self.assertTrue("major" in sev or "critical" in sev)


if __name__ == "__main__":
    unittest.main()
