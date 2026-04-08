from collections.abc import Callable
from dataclasses import dataclass
from random import Random
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .contracts import IncidentRecord, ScoreCard
from .scenario_bank import SCENARIOS


@dataclass(frozen=True)
class TruthProfile:
    classification: str
    suspect_drug: str
    severity_assessment: str
    recommended_action: str


class ScenarioSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, revalidate_instances="never")

    task_id: str = Field(...)
    difficulty: str = Field(...)
    reports: list[IncidentRecord] = Field(default_factory=list)
    drug_interaction_db: dict[str, Any] = Field(default_factory=dict)
    ground_truth: TruthProfile
    action_grader: Callable[[Any], ScoreCard]
    description: str = Field(default="")

    @property
    def id(self) -> str:
        return self.task_id


def _field_scores(action: Any, truth: TruthProfile) -> dict[str, float]:
    submitted = action.suspect_drug.strip().lower()
    expected = truth.suspect_drug.strip().lower()
    suspect_ok = submitted == expected or submitted in expected or expected in submitted

    scores = {
        "classification": 0.25 if action.classification == truth.classification else 0.0,
        "suspect_drug": 0.25 if suspect_ok else 0.0,
        "severity_assessment": 0.25 if action.severity_assessment == truth.severity_assessment else 0.0,
        "recommended_action": 0.25 if action.recommended_action == truth.recommended_action else 0.0,
        "false_alarm_penalty": 0.0,
        "missed_signal_penalty": 0.0,
        "reasoning_bonus": 0.0,
    }
    if action.classification == "new_signal" and truth.classification == "noise":
        scores["false_alarm_penalty"] = -0.10
    if action.classification == "noise" and truth.classification == "new_signal":
        scores["missed_signal_penalty"] = -0.20
    return scores


def _to_scorecard(scores: dict[str, float]) -> ScoreCard:
    total = round(sum(scores.values()), 4)
    return ScoreCard(total=max(0.0, min(1.0, total)), breakdown=scores)


def _grade_known(action: Any) -> ScoreCard:
    truth = TruthProfile(**SCENARIOS["known_signal_easy"]["ground_truth"])
    return _to_scorecard(_field_scores(action, truth))


def _grade_cluster(action: Any) -> ScoreCard:
    truth = TruthProfile(**SCENARIOS["cluster_signal_medium"]["ground_truth"])
    return _to_scorecard(_field_scores(action, truth))


def _grade_confounded(action: Any) -> ScoreCard:
    truth = TruthProfile(**SCENARIOS["confounded_hard"]["ground_truth"])
    scores = _field_scores(action, truth)
    note = action.reasoning.lower()
    bonus_terms = ("interaction", "flowmanager", "visionpatch", "latency", "queue", "monitoring")
    if any(term in note for term in bonus_terms):
        scores["reasoning_bonus"] = 0.15
    return _to_scorecard(scores)


def _from_payload(trajectory: Any = None) -> float:
    payload = trajectory or {}
    value = 0.5
    if isinstance(payload, dict):
        if "score" in payload:
            value = float(payload["score"])
        elif "rewards" in payload and payload["rewards"]:
            value = float(payload["rewards"][-1])
        elif "reward" in payload:
            reward_value = payload["reward"]
            if isinstance(reward_value, dict) and "total" in reward_value:
                value = float(reward_value["total"])
            else:
                value = float(reward_value)
    return max(0.01, min(0.99, round(value, 4)))


def known_signal_easy_grader(trajectory: Any = None) -> float:
    return _from_payload(trajectory)


def cluster_signal_medium_grader(trajectory: Any = None) -> float:
    return _from_payload(trajectory)


def confounded_hard_grader(trajectory: Any = None) -> float:
    return _from_payload(trajectory)


def _scenario(task_id: str, difficulty: str, description: str, grader: Callable[[Any], ScoreCard]) -> ScenarioSpec:
    source = SCENARIOS[task_id]
    return ScenarioSpec(
        task_id=task_id,
        difficulty=difficulty,
        reports=[IncidentRecord(**item) for item in source["reports"]],
        drug_interaction_db=source["drug_interaction_db"],
        ground_truth=TruthProfile(**source["ground_truth"]),
        action_grader=grader,
        description=description,
    )


def _all() -> dict[str, list[ScenarioSpec]]:
    return {
        "easy": [
            _scenario(
                "known_signal_easy",
                "easy",
                "Documented tunnel-navigation drift that should be logged, not escalated.",
                _grade_known,
            )
        ],
        "medium": [
            _scenario(
                "cluster_signal_medium",
                "medium",
                "Emerging warehouse autonomy freeze cluster that should be escalated.",
                _grade_cluster,
            )
        ],
        "hard": [
            _scenario(
                "confounded_hard",
                "hard",
                "Confounded sorting incident where the blamed OCR module is not the actual root cause.",
                _grade_confounded,
            )
        ],
    }


def get_tasks(difficulty: str | None = None, seed: int | None = None, n: int = 5, grouped: bool = False):
    catalog = _all()
    if difficulty is None:
        if grouped:
            return {level: items[:n] for level, items in catalog.items()}
        return {item.task_id: item for items in catalog.values() for item in items[:n]}

    choices = list(catalog.get(difficulty, []))
    if seed is not None:
        Random(seed).shuffle(choices)
    return choices[:n]


def get_task(task_id: str) -> ScenarioSpec:
    items = get_tasks()
    if task_id not in items:
        raise KeyError(f"Unknown task_id: {task_id}")
    return items[task_id]


known_signal_easy_action_grader = _grade_known
cluster_signal_medium_action_grader = _grade_cluster
confounded_hard_action_grader = _grade_confounded
