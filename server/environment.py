"""Medical Prior Authorization OpenEnv Environment."""

import re
import sys
import os
from typing import Any, Optional
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from openenv.core.env_server.interfaces import Environment
    from openenv.core.env_server.types import Action, Observation, State
except ImportError:
    from openenv.core.env_server.interfaces import Environment
    from openenv.core.env_server.types import Action, Observation, State

from models import PAAction, PAObservation, PAState
from tasks import TASKS, CLINICAL_GUIDELINES, FORMULARY, PATIENT_HISTORIES

TERMINAL_ACTIONS = {"approve", "deny", "request_info"}
ALL_ACTIONS = ["approve", "deny", "request_info", "lookup_guideline", "check_formulary", "get_patient_history"]


class MedPAEnvironment(Environment):

    def __init__(self):
        self._state = PAState()
        self._task_data: dict = {}
        self._ground_truth: dict = {}
        self._actions_taken: list[tuple[str, str]] = []
        self._guidelines_retrieved: list[dict] = []
        self._info_requested: list[str] = []
        self._formulary_checked: Optional[dict] = None
        self._history_retrieved: Optional[dict] = None
        self._done = False
        self._reward = 0.0

    def reset(self, seed=None, episode_id=None, task_id=None, **kwargs) -> Observation:
        tid = task_id or kwargs.get("task_id", "easy_knee_mri")
        if tid not in TASKS:
            tid = "easy_knee_mri"

        self._task_data = TASKS[tid]
        self._ground_truth = self._task_data["ground_truth"]
        self._actions_taken = []
        self._guidelines_retrieved = []
        self._info_requested = []
        self._formulary_checked = None
        self._history_retrieved = None
        self._done = False
        self._reward = 0.0
        self._state = PAState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=tid,
            current_step=0,
            max_steps=8,
            actions_taken=[],
        )

        req = self._task_data["request"]
        return PAObservation(
            request_id=req["request_id"], patient=req["patient"],
            diagnosis=req["diagnosis"], procedure=req["procedure"],
            clinical_notes=req["clinical_notes"],
            prior_treatments=req["prior_treatments"],
            attachments=req["attachments"],
            available_actions=ALL_ACTIONS, done=False, reward=0.0,
        )

    def step(self, action: Action, **kwargs) -> Observation:
        pa = action if isinstance(action, PAAction) else PAAction(**action.model_dump())

        self._state.step_count += 1
        self._state.current_step += 1
        self._state.actions_taken.append(pa.action_type)

        # Repeated action check
        sig = (pa.action_type, str(sorted(pa.payload.items())) if pa.payload else "")
        repeated = sig in self._actions_taken
        self._actions_taken.append(sig)
        penalty = -0.2 if repeated else 0.0

        result_text = None
        error_text = None

        if pa.action_type == "lookup_guideline":
            key = pa.payload.get("procedure") or pa.payload.get("diagnosis") or ""
            matches = [
                {"id": gid, **gdata}
                for gid, gdata in CLINICAL_GUIDELINES.items()
                if key in gdata.get("procedure_codes", []) or key in gdata.get("diagnosis_codes", [])
            ]
            if not matches and pa.payload.get("guideline_id"):
                gid = pa.payload["guideline_id"]
                if gid in CLINICAL_GUIDELINES:
                    matches = [{"id": gid, **CLINICAL_GUIDELINES[gid]}]
            self._guidelines_retrieved.extend(matches)
            result_text = f"Found {len(matches)} guideline(s)." if matches else "No matching guidelines."

        elif pa.action_type == "check_formulary":
            drug = (pa.payload.get("drug") or pa.payload.get("drug_name") or "").lower()
            entry = FORMULARY.get(drug)
            self._formulary_checked = entry
            result_text = f"Formulary: {entry}" if entry else f"No formulary entry for '{drug}'."

        elif pa.action_type == "get_patient_history":
            plan_id = self._task_data["request"]["patient"].get("plan_id", "")
            self._history_retrieved = PATIENT_HISTORIES.get(plan_id)
            result_text = f"History retrieved." if self._history_retrieved else "No history found."

        elif pa.action_type == "request_info":
            fields = pa.payload.get("fields", pa.payload.get("info_needed", []))
            self._info_requested.extend(fields)
            self._done = True
            total, breakdown, feedback = self._calculate_reward(pa)
            total += penalty
            self._reward = max(0.0, min(1.0, total))
            result_text = f"Requested info: {fields}. {feedback}"

        elif pa.action_type in ("approve", "deny"):
            self._done = True
            total, breakdown, feedback = self._calculate_reward(pa)
            total += penalty
            self._reward = max(0.0, min(1.0, total))
            result_text = f"Decision: {pa.action_type}. {feedback}"

        else:
            error_text = f"Unknown action: {pa.action_type}"

        # Non-terminal penalty
        if pa.action_type not in TERMINAL_ACTIONS and penalty:
            self._reward = max(0.0, self._reward + penalty)

        # Max steps
        if self._state.current_step >= self._state.max_steps and not self._done:
            self._done = True
            self._reward = max(0.0, min(1.0, self._reward + 0.05))
            result_text = (result_text or "") + " Max steps reached."

        req = self._task_data["request"]
        return PAObservation(
            request_id=req["request_id"], patient=req["patient"],
            diagnosis=req["diagnosis"], procedure=req["procedure"],
            clinical_notes=req["clinical_notes"],
            prior_treatments=req["prior_treatments"],
            attachments=req["attachments"],
            guidelines_retrieved=self._guidelines_retrieved,
            formulary_result=self._formulary_checked,
            patient_history=self._history_retrieved,
            last_action_result=result_text, last_action_error=error_text,
            available_actions=ALL_ACTIONS, done=self._done, reward=self._reward,
        )

    def _calculate_reward(self, action: PAAction) -> tuple[float, dict, str]:
        gt = self._ground_truth
        bd: dict[str, float] = {}
        fb: list[str] = []

        # Decision correctness (0.5)
        if action.action_type == gt["decision"]:
            if action.action_type == "deny" and gt.get("denial_reason_code"):
                code = action.payload.get("reason_code", "")
                if code == gt["denial_reason_code"]:
                    bd["decision"] = 0.5
                else:
                    bd["decision"] = 0.3
                    fb.append(f"Wrong reason code (expected {gt['denial_reason_code']}).")
            elif action.action_type == "request_info":
                required = set(gt.get("required_missing_fields", []))
                found = required & set(self._info_requested)
                bd["decision"] = 0.5 * (len(found) / len(required)) if required else 0.4
                if found != required:
                    fb.append(f"Missing fields: {required - found}")
            else:
                bd["decision"] = 0.5
        else:
            bd["decision"] = 0.0
            fb.append(f"Wrong decision (expected {gt['decision']}).")

        # Rationale quality (0.2)
        rationale = (action.rationale or "").lower()
        req_gl = gt.get("required_criteria", [])
        matched = sum(1 for g in req_gl if g.lower() in rationale)
        bd["rationale"] = 0.2 * (matched / len(req_gl)) if req_gl else (0.1 if rationale else 0.0)

        # Hallucination penalty
        cited = re.findall(r"gl-[\w-]+", rationale, re.IGNORECASE)
        for c in cited:
            if c.upper() not in CLINICAL_GUIDELINES:
                bd["rationale"] = max(0.0, bd["rationale"] - 0.3)
                fb.append(f"Hallucinated guideline: {c}.")
                break

        # Info quality (0.2)
        if gt["decision"] == "request_info":
            required = set(gt.get("required_missing_fields", []))
            found = required & set(self._info_requested)
            bd["info"] = 0.2 * (len(found) / len(required)) if required else 0.2
        else:
            bd["info"] = 0.2 if not self._info_requested else max(0.0, 0.2 - 0.05 * len(self._info_requested))

        # Efficiency (0.1)
        steps = self._state.current_step
        bd["efficiency"] = max(0.0, 0.1 * (1 - (steps - 1) / 7))

        total = max(0.0, min(1.0, sum(bd.values())))
        if not fb:
            fb.append("Correct.")
        return total, bd, " ".join(fb) + f" Score: {bd}"

    @property
    def state(self) -> PAState:
        return self._state

    def close(self):
        pass
