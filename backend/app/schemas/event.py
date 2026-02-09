from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    experiment_id: str
    user_id: str
    variant_id: str | None = None
    event_type: str = Field(pattern='^(exposure|conversion)$')
    period: str = Field(default='post', pattern='^(pre|post)$')
    value: float = 1.0


class EventResponse(BaseModel):
    id: str
    experiment_id: str
    user_id: str
    variant_id: str | None
    event_type: str
    period: str
    value: float

    model_config = {'from_attributes': True}
