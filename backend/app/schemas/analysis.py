from pydantic import BaseModel, Field


class AssignmentRequest(BaseModel):
    experiment_id: str
    unit_id: str = Field(min_length=1, max_length=120)
    attributes: dict | None = None


class AssignmentResponse(BaseModel):
    experiment_id: str
    assignment_id: str
    unit_id: str
    variant_key: str
    config_json: dict
    experiment_version: int
