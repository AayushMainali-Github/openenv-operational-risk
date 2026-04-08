from typing import Any

from .contracts import DecisionEnvelope, EpisodeView, ScoreCard
from .scoring import ScenarioSpec, get_task


class OperationsRiskEnv:
    def __init__(self) -> None:
        self.current_task: ScenarioSpec | None = None
        self.current_task_id: str | None = None
        self.step_number = 0
        self.max_steps = 1
        self.last_action: dict[str, Any] | None = None
        self.last_reward: dict[str, Any] | None = None

    def reset(self, task_id: str = "known_signal_easy") -> EpisodeView:
        self.current_task = get_task(task_id)
        self.current_task_id = self.current_task.task_id
        self.step_number = 0
        self.last_action = None
        self.last_reward = None
        return EpisodeView(
            task_id=self.current_task.task_id,
            reports=self.current_task.reports,
            drug_interaction_db=self.current_task.drug_interaction_db,
            step_number=self.step_number,
            max_steps=self.max_steps,
            feedback="Scenario loaded. Submit one final operational risk decision.",
        )

    def step(self, action: DecisionEnvelope):
        if self.current_task is None:
            raise RuntimeError("Call reset() before step().")

        score: ScoreCard = self.current_task.action_grader(action)
        self.step_number += 1
        self.last_action = action.model_dump()
        self.last_reward = score.model_dump()

        matched = sum(
            1
            for field_name in ("classification", "suspect_drug", "severity_assessment", "recommended_action")
            if score.breakdown.get(field_name, 0.0) > 0
        )

        if score.total >= 0.9:
            note = "Strong assessment. The main risk call and follow-up were aligned."
        elif score.total >= 0.5:
            note = "Partially correct assessment. The incident was interpreted only in part."
        else:
            note = "Weak assessment. Operations review would still be required."

        observation = EpisodeView(
            task_id=self.current_task.task_id,
            reports=self.current_task.reports,
            drug_interaction_db=self.current_task.drug_interaction_db,
            step_number=self.step_number,
            max_steps=self.max_steps,
            feedback=note,
        )
        info = {
            "matched_fields": matched,
            "difficulty": self.current_task.difficulty,
            "reward_breakdown": score.breakdown,
        }
        return observation, score, True, info

    def state(self) -> dict[str, Any]:
        return {
            "task_id": self.current_task_id,
            "step_number": self.step_number,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
        }
