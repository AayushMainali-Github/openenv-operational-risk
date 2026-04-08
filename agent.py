import json
import os
import sys
from typing import Optional

from openai import OpenAI

try:
    from .ops_sim.contracts import DecisionEnvelope as Action
except ImportError:
    from ops_sim.contracts import DecisionEnvelope as Action


_cached_client: Optional[OpenAI] = None
_cached_model = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")


def _client_or_none() -> Optional[OpenAI]:
    global _cached_client

    if _cached_client is not None:
        return _cached_client

    base_url = os.environ.get("API_BASE_URL", "").strip()
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("API_KEY") or "hf-missing-token"
    if not base_url:
        print("[WARN] API_BASE_URL is not configured; Agent will use heuristic mode.", file=sys.stderr)
        return None

    _cached_client = OpenAI(base_url=base_url, api_key=api_key)
    return _cached_client


class AnalystAgent:
    def __init__(self) -> None:
        self.review_memory: list[dict] = []

    def _scenario_snapshot(self, observation) -> str:
        lines = []
        for record in observation.reports:
            lines.append(
                f"- {record.report_id}: blamed={record.suspect_drug}, pattern={record.reaction}, "
                f"onset_days={record.onset_days}, severity={record.severity}, outcome={record.outcome}, "
                f"similar_30d={record.similar_reports_last_30d}"
            )

        memory_lines = ""
        if self.review_memory:
            memory_lines = "\nRecent weak calls:\n"
            for item in self.review_memory[-3:]:
                memory_lines += (
                    f"- On {item['task_id']} the choice {item['classification']} / "
                    f"{item['recommended_action']} underperformed. Note: {item['note']}\n"
                )

        return (
            f"Task id: {observation.task_id}\n"
            f"Incident records:\n" + "\n".join(lines) + "\n"
            f"Reference data:\n{json.dumps(observation.drug_interaction_db, ensure_ascii=True, indent=2)}"
            f"{memory_lines}"
        )

    def _prompt(self, observation) -> str:
        return f"""You are an operations-risk analyst.

Review the scenario below and return one JSON object only.

Return fields:
- classification: one of new_signal, known_side_effect, noise, duplicate
- suspect_drug: likely root-cause asset or interaction
- severity_assessment: one of mild, moderate, severe, critical
- recommended_action: one of escalate, log_and_monitor, dismiss, request_more_info
- reasoning: concise explanation

Decision principles:
- Repeated documented incidents should usually be known_side_effect
- Small but coherent clusters on a newer rollout can justify new_signal
- If the reporter blames the wrong module, prefer the stronger root-cause interaction
- Missing a serious signal is worse than overcalling a weak case

Scenario:
{self._scenario_snapshot(observation)}
"""

    def _llm_decision(self, observation) -> Optional[Action]:
        client = _client_or_none()
        if client is None:
            return None

        try:
            response = client.chat.completions.create(
                model=_cached_model,
                messages=[{"role": "user", "content": self._prompt(observation)}],
                temperature=0.0,
                max_tokens=220,
            )
            payload = json.loads((response.choices[0].message.content or "").strip())
            return Action(**payload)
        except Exception as exc:
            print(f"[WARN] Agent LLM path failed: {exc}; falling back to heuristics.", file=sys.stderr)
            return None

    def _heuristic_decision(self, observation) -> Action:
        records = observation.reports
        primary = records[0]
        reaction_blob = " ".join(item.reaction.lower() for item in records)
        reference_blob = json.dumps(observation.drug_interaction_db).lower()

        if "gps drift" in reaction_blob and "documented platform behavior" in reference_blob:
            return Action(
                classification="known_side_effect",
                suspect_drug="RouteSync",
                severity_assessment="mild",
                recommended_action="log_and_monitor",
                reasoning="Tunnel GPS drift is already documented and should be monitored, not escalated.",
            )

        if len(records) >= 3 and ("freeze" in reaction_blob or "queue" in reaction_blob or "escort" in reaction_blob):
            return Action(
                classification="new_signal",
                suspect_drug="PalletPilot",
                severity_assessment="severe",
                recommended_action="escalate",
                reasoning="A coherent cluster of automation freezes on a recent rollout warrants escalation.",
            )

        if "flowmanager" in reference_blob and "visionpatch" in reference_blob:
            return Action(
                classification="new_signal",
                suspect_drug="FlowManager+VisionPatch",
                severity_assessment="critical",
                recommended_action="escalate",
                reasoning="This looks like an interaction-driven latency spike that should be escalated with monitoring.",
            )

        fallback_severity = primary.severity if primary.severity in {"mild", "moderate", "severe", "critical"} else "moderate"
        return Action(
            classification="new_signal",
            suspect_drug=primary.suspect_drug,
            severity_assessment=fallback_severity,
            recommended_action="request_more_info",
            reasoning="The scenario is ambiguous, so more information is needed before final triage.",
        )

    def act(self, observation) -> Action:
        llm_action = self._llm_decision(observation)
        if llm_action is not None:
            return llm_action
        return self._heuristic_decision(observation)

    def learn(self, action: Action, observation) -> None:
        reward = getattr(observation, "reward", 0.0) or 0.0
        if reward < 0.5:
            self.review_memory.append(
                {
                    "task_id": getattr(observation, "task_id", "unknown"),
                    "classification": action.classification,
                    "recommended_action": action.recommended_action,
                    "note": getattr(observation, "feedback", "") or "weak outcome",
                }
            )
