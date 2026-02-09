from datetime import datetime

from pydantic import BaseModel, Field

from app.models.metric import GuardrailDirection, GuardrailStatus


class GuardrailMetricCreate(BaseModel):
    experiment_id: str
    name: str = Field(min_length=2, max_length=120)
    value: float
    threshold_value: float
    direction: GuardrailDirection


class GuardrailMetricResponse(BaseModel):
    id: str
    experiment_id: str
    name: str
    value: float
    threshold_value: float
    direction: GuardrailDirection
    status: GuardrailStatus
    observed_at: datetime

    model_config = {'from_attributes': True}
