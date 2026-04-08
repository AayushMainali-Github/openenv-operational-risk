from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncidentRecord(BaseModel):
    model_config = ConfigDict(revalidate_instances="never")

    report_id: str = Field(..., description="Unique incident ticket identifier")
    patient_age: int = Field(..., description="Legacy compatibility field storing operator or asset age")
    patient_sex: str = Field(..., description="Legacy compatibility field storing operator segment or fleet type")
    drugs: list[str] = Field(default_factory=list, description="Legacy compatibility field storing involved assets or services")
    suspect_drug: str = Field(..., description="Legacy compatibility field storing the initially blamed asset or service")
    reaction: str = Field(..., description="Observed incident pattern")
    onset_days: int = Field(..., description="Days from rollout or activation to incident onset")
    severity: str = Field(..., description="Reported business severity")
    outcome: str = Field(..., description="Current remediation state")
    similar_reports_last_30d: int = Field(..., description="Count of similar incidents observed recently")


class EpisodeView(BaseModel):
    task_id: str
    reports: list[IncidentRecord]
    drug_interaction_db: dict[str, Any]
    step_number: int
    max_steps: int
    feedback: str | None = None


class DecisionEnvelope(BaseModel):
    classification: str
    suspect_drug: str
    severity_assessment: str
    recommended_action: str
    reasoning: str


class ScoreCard(BaseModel):
    total: float = Field(..., ge=0.0, le=1.0)
    breakdown: dict[str, float]
