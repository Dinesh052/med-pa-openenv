from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional

from pydantic import Field, field_validator

try:
    from openenv.core.env_server.types import Action, Observation, State
except ImportError:
    from pydantic import BaseModel as Action, BaseModel as Observation, BaseModel as State


class PAAction(Action):
    action_type: Literal[
        "approve",
        "deny",
        "request_info",
        "lookup_guideline",
        "check_formulary",
        "get_patient_history",
    ] = Field(..., description="Type of action to perform")
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Action-specific payload. "
            "For deny: {reason_code: str}. "
            "For request_info: {fields: list[str]}. "
            "For lookup_guideline: {procedure: str, diagnosis: str}. "
            "For check_formulary: {drug: str}. "
            "For approve/get_patient_history: {} (empty)."
        ),
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Agent's rationale for the action. Required for approve/deny.",
    )

    @field_validator("payload", mode="before")
    @classmethod
    def _coerce_payload(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return {}
        return v if v is not None else {}


class PAObservation(Observation):
    request_id: str = Field(default="", description="Unique ID for this PA request")
    patient: dict = Field(default_factory=dict, description="Patient demographics (id, name, age, sex, insurance plan)")
    diagnosis: List[str] = Field(default_factory=list, description="ICD-10 diagnosis codes")
    procedure: str = Field(default="", description="CPT procedure code")
    clinical_notes: str = Field(default="", description="Free-text clinical notes from provider")
    prior_treatments: List[str] = Field(default_factory=list, description="Prior treatments the patient has received")
    attachments: List[str] = Field(default_factory=list, description="Documents attached to the request")

    # Dynamic fields populated by agent actions
    guideline_result: Optional[str] = Field(default=None, description="Result of the last guideline lookup")
    formulary_result: Optional[str] = Field(default=None, description="Result of the last formulary check")
    patient_history_result: Optional[str] = Field(default=None, description="Result of patient history retrieval")
    info_request_result: Optional[str] = Field(default=None, description="Result of requesting additional information")

    last_action_result: Optional[str] = Field(default=None, description="Result/status of the most recent action")
    last_action_error: Optional[str] = Field(default=None, description="Error from the most recent action, if any")
    available_actions: List[str] = Field(
        default_factory=lambda: [
            "approve", "deny", "request_info",
            "lookup_guideline", "check_formulary", "get_patient_history",
        ],
        description="Actions available to the agent",
    )

    step_number: int = Field(default=0, description="Current step in the episode")
    message: str = Field(default="", description="Human-readable status message")
    reward_breakdown: Optional[Dict[str, float]] = Field(
        default=None, description="Breakdown of reward components (terminal only)"
    )


class PAState(State):
    task_id: str = ""
    current_step: int = 0
    max_steps: int = 8
    actions_taken: List[str] = []
