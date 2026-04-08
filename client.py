# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Client for the operations-risk environment."""

from typing import Dict

try:
    from openenv.core import EnvClient
    from openenv.core.client_types import StepResult
    from openenv.core.env_server.types import State
except ImportError:
    class EnvClient:
        def __class_getitem__(cls, _item):
            return cls

    class StepResult:
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, observation, reward, done):
            self.observation = observation
            self.reward = reward
            self.done = done

    class State:
        def __init__(self, episode_id=None, step_count=0):
            self.episode_id = episode_id
            self.step_count = step_count

try:
    from .ops_sim.contracts import DecisionEnvelope as Action
    from .ops_sim.contracts import EpisodeView as Observation
    from .ops_sim.contracts import IncidentRecord as AdverseEventReport
except ImportError:
    from ops_sim.contracts import DecisionEnvelope as Action
    from ops_sim.contracts import EpisodeView as Observation
    from ops_sim.contracts import IncidentRecord as AdverseEventReport


class OpsRiskEnvClient(EnvClient[Action, Observation, State]):
    def _step_payload(self, action: Action) -> Dict:
        return {
            "classification": action.classification,
            "suspect_drug": action.suspect_drug,
            "severity_assessment": action.severity_assessment,
            "recommended_action": action.recommended_action,
            "reasoning": action.reasoning,
        }

    def _parse_result(self, payload: Dict) -> StepResult[Observation]:
        obs_data = payload.get("observation", {})
        reports = [AdverseEventReport(**report) for report in obs_data.get("reports", [])]

        observation = Observation(
            task_id=obs_data.get("task_id", ""),
            reports=reports,
            drug_interaction_db=obs_data.get("drug_interaction_db", {}),
            step_number=obs_data.get("step_number", 0),
            max_steps=obs_data.get("max_steps", 1),
            feedback=obs_data.get("feedback"),
        )

        reward_payload = payload.get("reward", 0.0)
        reward_total = reward_payload.get("total", 0.0) if isinstance(reward_payload, dict) else reward_payload

        return StepResult(
            observation=observation,
            reward=reward_total,
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("task_id", "ops-risk"),
            step_count=payload.get("step_number", 0),
        )
