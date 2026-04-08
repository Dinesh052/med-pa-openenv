"""Tests for grader.py — adapted to the actual grade_task() API."""

import pytest
from grader import grade_task, _normalize_ground_truth, GRADERS


# ── Helpers ──────────────────────────────────────────────────

def _make_gt(**overrides):
    """Build a minimal ground-truth dict with normalized keys."""
    gt = {
        "decision": "approve",
        "required_criteria": ["GL-KNEE-MRI-001"],
        "required_missing_fields": [],
        "denial_reason_code": None,
        "key_findings": ["positive Lachman test", "ACL disruption", "completed 6 weeks PT"],
    }
    gt.update(overrides)
    return gt


def _make_actions(*action_tuples):
    """Build actions list from (action_type, payload, rationale) tuples."""
    actions = []
    for tup in action_tuples:
        act_type = tup[0]
        payload = tup[1] if len(tup) > 1 else {}
        rationale = tup[2] if len(tup) > 2 else None
        actions.append({"action_type": act_type, "payload": payload, "rationale": rationale})
    return actions


# ── Tests ────────────────────────────────────────────────────

class TestCorrectApproveFullScore:
    def test_high_score_when_everything_correct(self):
        gt = _make_gt()
        actions = _make_actions(
            ("lookup_guideline", {"procedure": "73721"}),
            ("get_patient_history", {}),
            ("approve", {}, "Per GL-KNEE-MRI-001: positive Lachman test confirms ACL disruption. Patient completed 6 weeks PT with persistent instability."),
        )
        result = grade_task("easy_knee_mri", actions, gt)
        assert result["score"] >= 0.7
        assert result["breakdown"]["decision_correctness"] == 0.4
        assert result["breakdown"]["penalties"] == 0.0


class TestWrongDecision:
    def test_zero_correctness_when_wrong(self):
        gt = _make_gt()  # ground truth is "approve"
        actions = _make_actions(
            ("lookup_guideline", {"procedure": "73721"}),
            ("deny", {"reason_code": "CRITERIA_NOT_MET"}, "Criteria not met"),
        )
        result = grade_task("easy_knee_mri", actions, gt)
        assert result["breakdown"]["decision_correctness"] == 0.0


class TestRepeatedActionPenalty:
    def test_penalty_for_duplicate_action(self):
        gt = _make_gt()
        actions = _make_actions(
            ("lookup_guideline", {"procedure": "73721"}),
            ("lookup_guideline", {"procedure": "73721"}),  # exact duplicate
            ("approve", {}, "Per GL-KNEE-MRI-001: positive Lachman test, ACL disruption"),
        )
        result = grade_task("easy_knee_mri", actions, gt)
        assert result["breakdown"]["penalties"] < 0.0  # penalty applied


class TestNoTerminalAction:
    def test_score_001_when_no_decision(self):
        gt = _make_gt()
        actions = _make_actions(
            ("lookup_guideline", {"procedure": "73721"}),
            ("get_patient_history", {}),
        )
        result = grade_task("easy_knee_mri", actions, gt)
        assert result["score"] == 0.01


class TestMediumTaskRequestInfo:
    def test_request_info_is_correct_for_humira(self):
        gt = _make_gt(
            decision="request_info",
            required_criteria=["GL-BIOLOGIC-001"],
            required_missing_fields=["step_therapy_documentation", "prior_biologic_records"],
            key_findings=[
                "mesalamine failed",
                "prednisone dependent",
                "CDAI 285",
                "step therapy documentation missing",
                "prior biologic records not obtained",
            ],
            post_info_decision="approve",
        )
        actions = _make_actions(
            ("lookup_guideline", {"procedure": "J0135", "diagnosis": "K50.10"}),
            ("check_formulary", {"drug": "adalimumab"}),
            ("request_info", {"fields": ["step_therapy_documentation", "prior_biologic_records"]},
             "Per GL-BIOLOGIC-001: step therapy documentation and prior biologic records are required."),
        )
        result = grade_task("medium_humira", actions, gt)
        assert result["breakdown"]["info_request_quality"] > 0
        assert result["score"] >= 0.3


class TestHardDenialTask:
    def test_correct_denial_with_contraindication(self):
        gt = {
            "decision": "deny",
            "required_criteria": ["GL-SPINE-FUSION-001", "GL-SPINE-FUSION-002"],
            "required_missing_fields": [],
            "denial_reason_code": "CONTRAINDICATION_ACTIVE",
            "contraindication": {
                "type": "uncontrolled_diabetes",
                "detail": "HbA1c 8.4% > 8.0% threshold",
                "location_hint": "buried in comorbidities",
            },
            "key_findings": [
                "HbA1c 8.4% exceeds 8.0% threshold — uncontrolled diabetes",
                "primary care did not provide surgical clearance",
                "GL-SPINE-FUSION-001 requires no uncontrolled diabetes",
                "GL-SPINE-FUSION-002 has stricter BMI cutoff",
                "conservative treatment met",
                "psychological evaluation completed",
                "imaging concordant with symptoms",
            ],
            "alternative_denial_codes": ["CRITERIA_NOT_MET", "MEDICAL_NECESSITY_NOT_ESTABLISHED", "SAFETY_CONCERN"],
            "conflicting_guideline": {"primary": "GL-SPINE-FUSION-001", "secondary": "GL-SPINE-FUSION-002", "conflict": "..."},
        }
        actions = _make_actions(
            ("lookup_guideline", {"procedure": "22612"}),
            ("get_patient_history", {}),
            ("deny", {"reason_code": "CONTRAINDICATION_ACTIVE"},
             "Per GL-SPINE-FUSION-001: patient's HbA1c 8.4% exceeds 8.0% threshold. Uncontrolled diabetes is a contraindication. No surgical clearance from primary care."),
        )
        result = grade_task("hard_spinal_fusion", actions, gt)
        assert result["breakdown"]["decision_correctness"] == 0.15
        assert result["breakdown"]["contraindication_found"] >= 0.15
        assert result["score"] >= 0.3


class TestAllGradersMapped:
    def test_all_nine_tasks_have_graders(self):
        expected = [
            "easy_knee_mri", "easy_chest_xray", "easy_pt_eval",
            "medium_humira", "medium_ozempic", "medium_sleep_study",
            "hard_spinal_fusion", "hard_cardiac_cath", "hard_gene_therapy",
        ]
        for task_id in expected:
            assert task_id in GRADERS, f"Missing grader for {task_id}"


class TestNormalizeGroundTruth:
    def test_normalizes_task_format_to_grader_format(self):
        raw = {
            "decision": "deny",
            "required_criteria": ["GL-SPINE-FUSION-001", "GL-SPINE-FUSION-002"],
            "required_missing_fields": [],
            "denial_reason_code": "CONTRAINDICATION_ACTIVE",
            "conflicting_guideline": {"primary": "GL-SPINE-FUSION-001", "secondary": "GL-SPINE-FUSION-002"},
        }
        n = _normalize_ground_truth(raw)
        assert n["correct_decision"] == "deny"
        assert n["applicable_guideline"] == "GL-SPINE-FUSION-001"
        assert n["missing_fields"] == []
        assert n["correct_denial_code"] == "CONTRAINDICATION_ACTIVE"
        assert n["conflicting_guideline"] == "GL-SPINE-FUSION-002"
