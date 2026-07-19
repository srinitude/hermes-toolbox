import copy
import hashlib
import json
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/software-development/plan/scripts/validate_completion_report.py"
TEMPLATE = ROOT / "skills/software-development/plan/templates/completion-report.json"
VALIDATE = runpy.run_path(str(SCRIPT))["validate"]


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pass_report():
    report = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    report["plan"].update(path="plan.md", status="PASS", started_at="start", completed_at="end", status_reason="done")
    report["source_snapshot"][0].update(path_or_url="source", sha256_or_version="version", status="verified")
    report["baselines"][0].update(method="baseline", actual_exit_code=0, known_failure_signature="known")
    for group in ("tasks", "validators", "gates", "cleanup", "reviews"):
        report[group][0]["status"] = "PASS"
    report["requirements"][0].update(status="PASS", waiver_id=None)
    report["validators"][0].update(method="validate", working_directory=".", actual_exit_code=0, pass_condition="passes", actual_result="passed", evidence_ids=["EVID-001", "EVID-002"])
    report["gates"][0]["owner"] = "owner"
    report["risks"][0].update(status="mitigated", prevention_evidence="prevent", detection_evidence="detect", response_or_rollback_evidence="rollback", owner="owner")
    report["changed_files"][0]["path"] = "changed.txt"
    report["artifacts"][0].update(path="artifact.txt", exists=True)
    report["evidence"][0]["path"] = "evidence-1.json"
    report["waivers"] = []
    report["residual_risks"][0].update(description="risk", owner="owner", accepted_by="owner", revisit_condition="change")
    report["cleanup"][0].update(action="clean", result="clean")
    report["human_report"].update(path="human.json", status="PASS")
    report["checks"] = dict.fromkeys(report["checks"], True)
    report["check_evidence"]["independent_review_pass"] = ["EVID-002"]
    return report


def bind_evidence(root, item, validator):
    expected = {"evidence_id": item["id"], "validator_id": validator["id"], "validator_scope": validator["scope"], "validator_status": validator["status"], "expected_exit_code": validator["expected_exit_code"], "actual_exit_code": validator["actual_exit_code"], "actual_result": validator["actual_result"], "kind": item["kind"], "check_names": item["check_names"], "covers_ids": item["covers_ids"]}
    item["sha256"] = write_json(root / item["path"], expected)


def bind_proofs(root, report):
    artifact = root / "artifact.txt"
    artifact.write_text("artifact", encoding="utf-8")
    report["artifacts"][0]["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    validator = report["validators"][0]
    report["evidence"][0]["covers_ids"].remove("REVIEW-001")
    review = copy.deepcopy(report["evidence"][0])
    review.update(id="EVID-002", kind="review", check_names=["independent_review_pass"], covers_ids=["VAL-001", "REVIEW-001"], path="evidence-2.json")
    report["evidence"].append(review)
    report["reviews"][0]["evidence_ids"] = ["EVID-002"]
    for item in report["evidence"]:
        bind_evidence(root, item, validator)
    human = {"plan_id": report["plan"]["id"], "status": "PASS", "checks": report["checks"], "check_evidence": report["check_evidence"]}
    report["human_report"]["sha256"] = write_json(root / "human.json", human)


class CompletionReportTests(unittest.TestCase):
    def test_template_is_blocked_by_cli(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), str(TEMPLATE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stderr.splitlines())
        self.assertTrue(all(line.startswith("BLOCKED: ") for line in result.stderr.splitlines()))

    def test_complete_report_passes(self):
        with tempfile.TemporaryDirectory(prefix="completion-report-test-") as raw:
            report = pass_report()
            bind_proofs(Path(raw), report)
            self.assertEqual([], VALIDATE(report, Path(raw) / "report.json"))

    def test_nonreciprocal_link_is_blocked(self):
        report = pass_report()
        report["requirements"][0]["task_ids"] = []
        self.assertTrue(any("reciprocal" in error for error in VALIDATE(report, TEMPLATE)))


class EvidenceReciprocityTests(unittest.TestCase):
    def test_forged_evidence_coverage_is_blocked(self):
        with tempfile.TemporaryDirectory(prefix="completion-report-test-") as raw:
            root = Path(raw)
            report = pass_report()
            bind_proofs(root, report)
            forged = report["evidence"][1]
            forged["covers_ids"].append("TASK-001")
            bind_evidence(root, forged, report["validators"][0])
            self.assertTrue(any("provenance" in error for error in VALIDATE(report, root / "report.json")))


class MalformedCompletionReportTests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_malformed_fields_are_blocked_without_crashing(self):
        cases = (
            ("evidence", "covers_ids", 1),
            ("evidence", "check_names", None),
            ("requirements", "task_ids", None),
            ("validators", "evidence_ids", None),
            ("evidence", "kind", {}),
            ("evidence", "validator_id", {}),
        )
        for group, key, value in cases:
            with self.subTest(group=group, key=key):
                report = copy.deepcopy(self.report)
                report[group][0][key] = value
                self.assertTrue(VALIDATE(report, TEMPLATE))


if __name__ == "__main__":
    unittest.main()
