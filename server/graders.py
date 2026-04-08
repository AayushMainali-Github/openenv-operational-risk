"""Trajectory scorers for the operations-risk environment."""

from collections.abc import Iterable


STRICT_MIN = 0.01
STRICT_MAX = 0.99


def _clamp(value: float) -> float:
    return min(max(round(value, 4), STRICT_MIN), STRICT_MAX)


def _reward_values(trajectory: dict | None) -> list[float]:
    payload = trajectory or {}

    rewards = payload.get("rewards")
    if isinstance(rewards, list) and rewards:
        return [float(item) for item in rewards]

    if "score" in payload:
        return [float(payload["score"])]

    reward = payload.get("reward")
    if isinstance(reward, dict) and "total" in reward:
        return [float(reward["total"])]
    if reward is not None:
        return [float(reward)]

    return []


def _band(reward: float) -> str:
    if reward <= 0.05:
        return "unsafe_miss"
    if reward <= 0.20:
        return "bad_call"
    if reward < 0.50:
        return "weak_triage"
    if reward < 0.80:
        return "workable_triage"
    if reward < 0.95:
        return "strong_triage"
    return "expert_triage"


def _mean(values: Iterable[float]) -> float:
    bucket = list(values)
    if not bucket:
        return 0.5
    return sum(bucket) / len(bucket)


def _episode_score(
    rewards: list[float],
    *,
    miss_cost: float,
    overcall_cost: float,
    stability_gain: float,
    expertise_gain: float,
) -> float:
    if not rewards:
        return 0.5

    bands = [_band(reward) for reward in rewards]
    mean_reward = _mean(rewards)
    step_count = len(rewards)

    missed = bands.count("unsafe_miss")
    overcalled = bands.count("bad_call")
    weak = bands.count("weak_triage")
    strong = bands.count("strong_triage") + bands.count("expert_triage")
    expert = bands.count("expert_triage")

    penalty = min(missed * miss_cost, 0.35) + min(overcalled * overcall_cost, 0.15) + min(weak * 0.015, 0.06)
    bonus = 0.0
    if strong / step_count >= 0.80:
        bonus += stability_gain
    if expert / step_count >= 0.60:
        bonus += expertise_gain

    return _clamp(mean_reward - penalty + bonus)


def easy_grader(trajectory: dict = None) -> float:
    return _episode_score(
        _reward_values(trajectory),
        miss_cost=0.12,
        overcall_cost=0.03,
        stability_gain=0.05,
        expertise_gain=0.01,
    )


def medium_grader(trajectory: dict = None) -> float:
    return _episode_score(
        _reward_values(trajectory),
        miss_cost=0.09,
        overcall_cost=0.04,
        stability_gain=0.03,
        expertise_gain=0.02,
    )


def hard_grader(trajectory: dict = None) -> float:
    return _episode_score(
        _reward_values(trajectory),
        miss_cost=0.07,
        overcall_cost=0.03,
        stability_gain=0.02,
        expertise_gain=0.04,
    )


def known_signal_easy_grader(trajectory: dict = None) -> float:
    return easy_grader(trajectory)


def cluster_signal_medium_grader(trajectory: dict = None) -> float:
    return medium_grader(trajectory)


def confounded_hard_grader(trajectory: dict = None) -> float:
    return hard_grader(trajectory)
