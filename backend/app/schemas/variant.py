import json

from pydantic import BaseModel, Field, model_validator


class VariantCreate(BaseModel):
    key: str | None = Field(default=None, min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    weight: float | None = Field(default=None, gt=0, le=1)
    config_json: dict = Field(default_factory=dict)
    # Backward-compatible alias used by older callers.
    traffic_allocation: float | None = Field(default=None, gt=0, le=1)

    @model_validator(mode='after')
    def normalize_fields(self):
        if self.weight is None and self.traffic_allocation is not None:
            self.weight = self.traffic_allocation
        if self.weight is None:
            raise ValueError('Variant weight is required')
        if self.key is None:
            normalized = self.name.strip().lower().replace(' ', '_').replace('-', '_')
            self.key = normalized or 'variant'
        return self

    def to_config_json(self) -> str:
        return json.dumps(self.config_json)


class VariantResponse(BaseModel):
    id: str
    key: str
    name: str
    weight: float
    config_json: dict
    traffic_allocation: float

    model_config = {'from_attributes': True}
