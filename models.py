from __future__ import annotations
from typing import Literal

try:
    from openenv.core.env_server.types import Action, Observation, State
except ImportError:
    from openenv.core.env_server.types import Action, Observation, State


class PAAction(Action):
    action_type: Literal[
        "approve",
        "deny",
        "request_info",
        "lookup_guideline",
        "check_formulary",
        "get_patient_history",
    ]
    payload: dict = {}
    rationale: str | None = None


class PAObservation(Observation):
    request_id: str
    patient: dict
    diagnosis: list[str]
    procedure: str
    clinical_notes: str
    prior_treatments: list[str]
    attachments: list[str]
    guidelines_retrieved: list[dict] = []
    formulary_result: dict | None = None
    patient_history: dict | None = None
    last_action_result: str | None = None
    last_action_error: str | None = None
    available_actions: list[str]


class PAState(State):
    task_id: str = ""
    current_step: int = 0
    max_steps: int = 8
    actions_taken: list[str] = []
