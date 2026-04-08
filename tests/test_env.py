import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ops_sim.contracts import DecisionEnvelope as Action
from ops_sim.runtime import OperationsRiskEnv as OpsRiskEnv
from ops_sim.scoring import (
    cluster_signal_medium_action_grader,
    cluster_signal_medium_grader,
    confounded_hard_action_grader,
    confounded_hard_grader,
    get_task,
    get_tasks,
    known_signal_easy_action_grader,
    known_signal_easy_grader,
)


def test_reset_loads_easy_task():
    env = OpsRiskEnv()
    obs = env.reset("known_signal_easy")
    assert obs.task_id == "known_signal_easy"
    assert obs.step_number == 0
    assert len(obs.reports) == 1


def test_known_signal_grader_full_credit():
    reward = known_signal_easy_action_grader(
        Action(
            classification="known_side_effect",
            suspect_drug="RouteSync",
            severity_assessment="mild",
            recommended_action="log_and_monitor",
            reasoning="This is a documented tunnel-navigation issue.",
        )
    )
    assert reward.total == 1.0


def test_medium_cluster_grader_partial_credit():
    reward = cluster_signal_medium_action_grader(
        Action(
            classification="new_signal",
            suspect_drug="PalletPilot",
            severity_assessment="moderate",
            recommended_action="escalate",
            reasoning="A cluster is forming around the new rollout.",
        )
    )
    assert reward.total == 0.75


def test_hard_grader_reasoning_bonus():
    reward = confounded_hard_action_grader(
        Action(
            classification="new_signal",
            suspect_drug="FlowManager+VisionPatch",
            severity_assessment="critical",
            recommended_action="escalate",
            reasoning="This looks like a FlowManager and VisionPatch interaction with queue monitoring signals.",
        )
    )
    assert reward.total == 1.0
    assert reward.breakdown["reasoning_bonus"] == 0.15


def test_hard_grader_substring_suspect_match():
    reward = confounded_hard_action_grader(
        Action(
            classification="new_signal",
            suspect_drug="FlowManager",
            severity_assessment="critical",
            recommended_action="escalate",
            reasoning="VisionPatch likely triggered the queue latency spike.",
        )
    )
    assert reward.breakdown["suspect_drug"] == 0.25


def test_env_step_returns_done():
    env = OpsRiskEnv()
    env.reset("confounded_hard")
    obs, reward, done, info = env.step(
        Action(
            classification="new_signal",
            suspect_drug="FlowManager+VisionPatch",
            severity_assessment="critical",
            recommended_action="escalate",
            reasoning="Interaction-driven queue overload needs escalation.",
        )
    )
    assert done is True
    assert obs.step_number == 1
    assert "reward_breakdown" in info
    assert reward.total >= 0.85


def test_state_tracks_last_action():
    env = OpsRiskEnv()
    env.reset("known_signal_easy")
    env.step(
        Action(
            classification="known_side_effect",
            suspect_drug="RouteSync",
            severity_assessment="mild",
            recommended_action="log_and_monitor",
            reasoning="Known tunnel drift behavior.",
        )
    )
    state = env.state()
    assert state["step_number"] == 1
    assert state["last_action"]["classification"] == "known_side_effect"


def test_all_tasks_available():
    tasks = get_tasks()
    assert set(tasks.keys()) == {"known_signal_easy", "cluster_signal_medium", "confounded_hard"}


def test_get_task_returns_hard_truth():
    task = get_task("confounded_hard")
    assert task.ground_truth.suspect_drug == "FlowManager+VisionPatch"


def test_public_graders_are_strictly_bounded():
    assert known_signal_easy_grader({"rewards": [1.0]}) == 0.99
    assert cluster_signal_medium_grader({"rewards": [0.0]}) == 0.01
    assert confounded_hard_grader({"score": 1.5}) == 0.99


def test_http_reset_then_step_roundtrip():
    pytest.importorskip("openenv")
    from fastapi.testclient import TestClient
    from server.app import app

    client = TestClient(app)

    reset_response = client.post("/reset", json={})
    assert reset_response.status_code == 200

    step_response = client.post(
        "/step",
        json={
            "action": {
                "classification": "known_side_effect",
                "suspect_drug": "RouteSync",
                "severity_assessment": "mild",
                "recommended_action": "log_and_monitor",
                "reasoning": "Known tunnel guidance drift.",
            }
        },
    )
    assert step_response.status_code == 200
    payload = step_response.json()
    assert payload["done"] is True
    assert payload["reward"] == 1.0
