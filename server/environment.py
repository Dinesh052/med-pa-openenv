"""Medical Prior Authorization OpenEnv Environment."""

import sys
import os
from typing import Any, Optional
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openenv.core.env_server.interfaces import Environment
from models import PAAction, PAObservation, PAState
from tasks import TASKS, CLINICAL_GUIDELINES, FORMULARY, PATIENT_HISTORIES
from grader import grade_task

MAX_STEPS = 8
TERMINAL_ACTIONS = {"approve", "deny", "request_info"}
ALL_ACTIONS = ["approve", "deny", "request_info", "lookup_guideline", "check_formulary", "get_patient_history"]


class MedPAEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = PAState()
        self._task_data: dict = {}
        self._task_id: str = ""
        self._actions_taken: list[dict[str, Any]] = []
        self._done = False
        self._guideline_result: Optional[str] = None
        self._formulary_result: Optional[str] = None
        self._patient_history_result: Optional[str] = None
        self._info_request_result: Optional[str] = None

    def reset(self, seed=None, episode_id=None, task_id=None, **kwargs) -> PAObservation:
        tid = task_id or kwargs.get("task_id", "easy_knee_mri")
        if tid not in TASKS:
            tid = "easy_knee_mri"

        self._task_id = tid
        self._task_data = TASKS[tid]
        self._actions_taken = []
        self._done = False
        self._guideline_result = None
        self._formulary_result = None
        self._patient_history_result = None
        self._info_request_result = None
        self._state = PAState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=tid,
            current_step=0,
            max_steps=MAX_STEPS,
            actions_taken=[],
        )

        req = self._task_data["request"]
        return PAObservation(
            request_id=req["request_id"],
            patient=req["patient"],
            diagnosis=req["diagnosis"],
            procedure=req["procedure"],
            clinical_notes=req["clinical_notes"],
            prior_treatments=req["prior_treatments"],
            attachments=req["attachments"],
            available_actions=ALL_ACTIONS,
            message=f"PA request {req['request_id']} loaded. Review the case and make a decision.",
            done=False,
            reward=0.0,
        )

    def step(self, action, **kwargs) -> PAObservation:
        pa = action if isinstance(action, PAAction) else PAAction(**action.model_dump())

        if self._done:
            return PAObservation(message="Episode already finished.", done=True, reward=0.0)

        self._state.step_count += 1
        self._state.current_step += 1
        self._state.actions_taken.append(pa.action_type)

        self._actions_taken.append({
            "action_type": pa.action_type,
            "payload": pa.payload,
            "rationale": pa.rationale,
            "step": self._state.current_step,
        })

        req = self._task_data["request"]
        step_num = self._state.current_step

        handlers = {
            "lookup_guideline": self._handle_lookup_guideline,
            "check_formulary": self._handle_check_formulary,
            "get_patient_history": self._handle_get_patient_history,
            "request_info": self._handle_request_info,
            "approve": self._handle_decision,
            "deny": self._handle_decision,
        }
        handler = handlers.get(pa.action_type)
        if handler is None:
            return self._make_observation(req, f"Unknown action: {pa.action_type}", 0.0)

        return handler(pa, req, step_num)

    # ── Handlers ──────────────────────────────────────────

    def _handle_lookup_guideline(self, action: PAAction, req: dict, step_num: int) -> PAObservation:
        payload = action.payload
        proc = payload.get("procedure", req["procedure"])
        diag = payload.get("diagnosis", req["diagnosis"][0] if req["diagnosis"] else "")
        gid = payload.get("guideline_id")

        matches = []
        for gl_id, gl in CLINICAL_GUIDELINES.items():
            if gid and gl_id == gid:
                matches.append((gl_id, gl))
            elif proc in gl.get("procedure_codes", []) or diag in gl.get("diagnosis_codes", []):
                matches.append((gl_id, gl))

        if matches:
            parts = []
            for gl_id, gl in matches:
                criteria = "\n".join(f"  - {c}" for c in gl["criteria"])
                parts.append(f"Guideline {gl_id}: {gl['name']}\nCriteria:\n{criteria}")
            self._guideline_result = "\n\n".join(parts)
        else:
            self._guideline_result = f"No guidelines found for procedure {proc} / diagnosis {diag}."

        if step_num >= MAX_STEPS:
            return self._force_end(req, "Step limit reached without a decision.")
        return self._make_observation(req, "Guideline lookup complete.", 0.0)

    def _handle_check_formulary(self, action: PAAction, req: dict, step_num: int) -> PAObservation:
        drug = (action.payload.get("drug") or action.payload.get("drug_name") or "").lower()
        entry = FORMULARY.get(drug)

        if entry:
            self._formulary_result = (
                f"Drug: {drug}\nTier: {entry['tier']}\n"
                f"Requires PA: {entry['requires_pa']}\n"
                f"Step therapy required: {entry['step_therapy_required']}\n"
                f"Alternatives: {', '.join(entry.get('alternatives', []))}"
            )
        else:
            self._formulary_result = f"Drug '{drug}' not found in formulary."

        if step_num >= MAX_STEPS:
            return self._force_end(req, "Step limit reached without a decision.")
        return self._make_observation(req, "Formulary check complete.", 0.0)

    def _handle_get_patient_history(self, action: PAAction, req: dict, step_num: int) -> PAObservation:
        plan_id = req["patient"].get("plan_id", "")
        history = PATIENT_HISTORIES.get(plan_id)

        if history:
            auths = "\n".join(
                f"  - {pa['request_id']}: {pa['procedure']} → {pa['decision']} ({pa['date']})"
                for pa in history.get("prior_authorizations", [])
            ) or "  None"
            conditions = ", ".join(history.get("chronic_conditions", [])) or "None"
            self._patient_history_result = f"Prior Authorizations:\n{auths}\nChronic Conditions: {conditions}"
        else:
            self._patient_history_result = "No patient history found."

        if step_num >= MAX_STEPS:
            return self._force_end(req, "Step limit reached without a decision.")
        return self._make_observation(req, "Patient history retrieved.", 0.0)

    def _handle_request_info(self, action: PAAction, req: dict, step_num: int) -> PAObservation:
        fields = action.payload.get("fields", action.payload.get("info_needed", []))
        if not fields:
            return self._make_observation(req, "Error: request_info requires 'fields' in payload.", 0.0)

        supplemental = self._task_data.get("supplemental_info", {})
        results = []
        for field in fields:
            if field in supplemental:
                results.append(f"[{field}]: {supplemental[field]}")
            else:
                results.append(f"[{field}]: Document not available.")
        self._info_request_result = "\n\n".join(results)

        # request_info is terminal
        self._done = True
        return self._grade_and_respond(action, req, f"Requested info: {fields}.")

    def _handle_decision(self, action: PAAction, req: dict, step_num: int) -> PAObservation:
        self._done = True
        return self._grade_and_respond(action, req, f"Decision: {action.action_type}.")

    # ── Helpers ───────────────────────────────────────────

    def _grade_and_respond(self, action: PAAction, req: dict, msg_prefix: str) -> PAObservation:
        gt = self._task_data["ground_truth"]
        try:
            result = grade_task(self._task_id, self._actions_taken, gt, MAX_STEPS)
            score = max(0.01, min(0.99, result["score"]))
            breakdown = result["breakdown"]
            feedback = result["feedback"]
        except (ValueError, KeyError):
            score, breakdown, feedback = self._fallback_grade(action, gt)

        return PAObservation(
            request_id=req["request_id"],
            patient=req["patient"],
            diagnosis=req["diagnosis"],
            procedure=req["procedure"],
            clinical_notes=req["clinical_notes"],
            prior_treatments=req["prior_treatments"],
            attachments=req["attachments"],
            guideline_result=self._guideline_result,
            formulary_result=self._formulary_result,
            patient_history_result=self._patient_history_result,
            info_request_result=self._info_request_result,
            available_actions=ALL_ACTIONS,
            message=f"{msg_prefix} {feedback}",
            reward_breakdown=breakdown,
            done=True,
            reward=score,
        )

    def _fallback_grade(self, action: PAAction, gt: dict) -> tuple[float, dict, str]:
        """Simple fallback grader for tasks not in the grader registry."""
        bd: dict[str, float] = {}
        correct = action.action_type == gt["decision"]
        bd["decision"] = 0.5 if correct else 0.0
        bd["efficiency"] = max(0.0, 0.1 * (1 - (self._state.current_step - 1) / 7))
        bd["rationale"] = 0.1 if action.rationale else 0.0
        bd["info"] = 0.2 if any(a["action_type"] in ("lookup_guideline", "check_formulary", "get_patient_history") for a in self._actions_taken) else 0.0
        total = max(0.01, min(0.99, sum(bd.values())))
        fb = "Correct." if correct else f"Wrong decision (expected {gt['decision']})."
        return total, bd, fb

    def _force_end(self, req: dict, message: str) -> PAObservation:
        self._done = True
        gt = self._task_data["ground_truth"]
        try:
            result = grade_task(self._task_id, self._actions_taken, gt, MAX_STEPS)
            score = max(0.01, min(0.99, result["score"]))
            breakdown = result["breakdown"]
        except (ValueError, KeyError):
            score, breakdown = 0.05, {"timeout": 0.05}

        return PAObservation(
            request_id=req["request_id"],
            patient=req["patient"],
            diagnosis=req["diagnosis"],
            procedure=req["procedure"],
            clinical_notes=req["clinical_notes"],
            prior_treatments=req["prior_treatments"],
            attachments=req["attachments"],
            guideline_result=self._guideline_result,
            formulary_result=self._formulary_result,
            patient_history_result=self._patient_history_result,
            info_request_result=self._info_request_result,
            available_actions=ALL_ACTIONS,
            message=message,
            reward_breakdown=breakdown,
            done=True,
            reward=score,
        )

    def _make_observation(self, req: dict, message: str, reward: float) -> PAObservation:
        return PAObservation(
            request_id=req["request_id"],
            patient=req["patient"],
            diagnosis=req["diagnosis"],
            procedure=req["procedure"],
            clinical_notes=req["clinical_notes"],
            prior_treatments=req["prior_treatments"],
            attachments=req["attachments"],
            guideline_result=self._guideline_result,
            formulary_result=self._formulary_result,
            patient_history_result=self._patient_history_result,
            info_request_result=self._info_request_result,
            available_actions=ALL_ACTIONS,
            message=message,
            done=False,
            reward=reward,
        )

    @property
    def state(self) -> PAState:
        return self._state

    def close(self):
        pass
