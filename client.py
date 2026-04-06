"""Medical Prior Authorization OpenEnv Client."""

from typing import Any, Dict

try:
    from openenv.core.env_client import EnvClient
    from openenv.core.client_types import StepResult
except ImportError:
    from openenv.core.env_client import EnvClient
    from openenv.core.client_types import StepResult

from models import PAAction, PAObservation, PAState


class MedPAEnv(EnvClient[PAAction, PAObservation, PAState]):
    """Client for the Medical Prior Authorization environment."""

    def _step_payload(self, action: PAAction) -> Dict[str, Any]:
        return action.model_dump(exclude={"metadata"})

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[PAObservation]:
        obs_data = payload.get("observation", payload)
        return StepResult(
            observation=PAObservation(**obs_data),
            reward=payload.get("reward") or obs_data.get("reward") or 0.0,
            done=payload.get("done", obs_data.get("done", False)),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> PAState:
        return PAState(**payload)
