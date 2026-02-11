from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    experiment_id: str
    user_id: str
    variant_id: str | None = None
    event_type: str = Field(pattern='^(exposure|conversion|metric)$')
    metric_name: str | None = None
    period: str = Field(default='post', pattern='^(pre|post)$')
    value: float = 1.0
    context_json: dict | None = None
    observed_at: datetime | None = None


class EventResponse(BaseModel):
    id: str
    experiment_id: str
    user_id: str
    variant_id: str | None
    event_type: str
    metric_name: str | None
    period: str
    value: float
    context_json: dict
    observed_at: datetime

    model_config = {'from_attributes': True}


class ExposureEventCreate(BaseModel):
    experiment_id: str
    unit_id: str
    variant_key: str
    ts: datetime | None = None
    context: dict | None = None


class MetricEventCreate(BaseModel):
    experiment_id: str
    unit_id: str
    variant_key: str
    metric_name: str = Field(min_length=1, max_length=120)
    value: float
    ts: datetime | None = None
    context: dict | None = None


class BatchIngestResponse(BaseModel):
    ingested: int
