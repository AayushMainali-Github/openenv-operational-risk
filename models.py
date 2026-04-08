from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

try:
    from openenv.core.env_server.types import Action, Observation
except ImportError:
    class Action(BaseModel):
        pass

    class Observation(BaseModel):
        pass

from ops_sim.contracts import IncidentRecord


class AdverseEventReport(IncidentRecord):
    pass


class OpsObservation(Observation):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=True,
        revalidate_instances="never",
    )

    task_id: str = Field(..., description="Current scenario identifier")
    reports: list[AdverseEventReport] = Field(default_factory=list, description="Incident bundle for the scenario")
    drug_interaction_db: dict = Field(default_factory=dict, description="Compatibility field containing operational reference context")
    step_number: int = Field(default=0, description="Current step number")
    max_steps: int = Field(default=1, description="Maximum number of steps in the episode")
    feedback: Optional[str] = Field(default=None, description="Feedback after the previous action")

    reward: float = Field(default=0.0, description="Reward from the last action")
    done: bool = Field(default=False, description="Episode termination flag")
    metadata: dict = Field(default_factory=dict, description="Additional environment metadata")


class OpsAction(Action):
    classification: str = Field(..., description="known_side_effect, new_signal, noise, or duplicate")
    suspect_drug: str = Field(..., description="Compatibility field for the likely root-cause asset or interaction")
    severity_assessment: str = Field(..., description="mild, moderate, severe, or critical")
    recommended_action: str = Field(..., description="escalate, log_and_monitor, dismiss, or request_more_info")
    reasoning: str = Field(default="", description="Concise explanation of the decision")
