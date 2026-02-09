from datetime import datetime

from pydantic import BaseModel, Field

from app.models.experiment import ExperimentStatus


class DecisionOverrideRequest(BaseModel):
    status: ExperimentStatus
    reason: str | None = Field(default=None, max_length=1000)
    actor: str = Field(default='operator', min_length=2, max_length=120)


class DecisionAuditResponse(BaseModel):
    id: str
    experiment_id: str
    previous_status: str
    new_status: str
    reason: str | None
    source: str
    actor: str
    created_at: datetime

    model_config = {'from_attributes': True}
