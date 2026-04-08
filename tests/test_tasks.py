"""Tests for tasks.py — structure validation and randomization."""

import pytest
from tasks import TASKS, CLINICAL_GUIDELINES, FORMULARY, PATIENT_HISTORIES, get_randomized_task


class TestAllTasksHaveRequiredFields:
    @pytest.mark.parametrize("task_id", list(TASKS.keys()))
    def test_required_sections_exist(self, task_id):
        task = TASKS[task_id]
        assert "request" in task, f"{task_id} missing 'request'"
        assert "ground_truth" in task, f"{task_id} missing 'ground_truth'"
        assert "patient_history" in task, f"{task_id} missing 'patient_history'"

    @pytest.mark.parametrize("task_id", list(TASKS.keys()))
    def test_ground_truth_valid_decision(self, task_id):
        gt = TASKS[task_id]["ground_truth"]
        assert gt["decision"] in {"approve", "deny", "request_info"}, (
            f"{task_id} has invalid decision: {gt['decision']}"
        )
        assert len(gt["required_criteria"]) >= 1, (
            f"{task_id} has no required_criteria"
        )


class TestAllRequiredCriteriaAreValidGuidelineIds:
    @pytest.mark.parametrize("task_id", list(TASKS.keys()))
    def test_criteria_reference_real_guidelines(self, task_id):
        criteria = TASKS[task_id]["ground_truth"]["required_criteria"]
        for gl_id in criteria:
            assert gl_id in CLINICAL_GUIDELINES, (
                f"{task_id} references unknown guideline {gl_id}"
            )


class TestAllPlanIdsAreUnique:
    def test_no_duplicate_plan_ids_across_tasks(self):
        plan_ids = []
        for task_id, task in TASKS.items():
            pid = task["request"]["patient"]["plan_id"]
            plan_ids.append((task_id, pid))

        seen = {}
        for task_id, pid in plan_ids:
            if pid in seen:
                pytest.fail(
                    f"plan_id {pid} reused by {seen[pid]} and {task_id} — "
                    f"agents would get wrong PATIENT_HISTORIES"
                )
            seen[pid] = task_id

    def test_all_plan_ids_have_history_entries(self):
        for task_id, task in TASKS.items():
            pid = task["request"]["patient"]["plan_id"]
            assert pid in PATIENT_HISTORIES, (
                f"{task_id} plan_id {pid} not in PATIENT_HISTORIES"
            )


class TestRandomizedTaskPreservesGroundTruth:
    @pytest.mark.parametrize("task_id", [
        "easy_knee_mri", "hard_spinal_fusion", "medium_humira", "hard_cardiac_cath",
    ])
    def test_ground_truth_preserved(self, task_id):
        original = TASKS[task_id]
        rand42 = get_randomized_task(task_id, seed=42)
        rand99 = get_randomized_task(task_id, seed=99)

        # Ground truth decision must be identical
        assert rand42["ground_truth"]["decision"] == original["ground_truth"]["decision"]
        assert rand99["ground_truth"]["decision"] == original["ground_truth"]["decision"]

        # The two randomized versions should differ in at least one field
        assert (
            rand42["request"]["clinical_notes"] != rand99["request"]["clinical_notes"]
            or rand42["request"]["patient"]["age"] != rand99["request"]["patient"]["age"]
        )


class TestFormularyStepTherapyConsistency:
    def test_step_therapy_drugs_are_known(self):
        """Step therapy drugs should either be in FORMULARY or be well-known
        conventional therapies (e.g. azathioprine, glipizide) that don't require
        PA and thus aren't tracked in the specialty formulary."""
        known_conventional = {"azathioprine", "glipizide", "metformin"}
        for drug_name, entry in FORMULARY.items():
            for step_drug in entry.get("step_therapy", []):
                assert step_drug in FORMULARY or step_drug in known_conventional, (
                    f"Formulary '{drug_name}' has step_therapy '{step_drug}' "
                    f"which is neither in FORMULARY nor a known conventional therapy"
                )
