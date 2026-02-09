from pydantic import BaseModel


class AssignmentRequest(BaseModel):
    experiment_id: str
    user_id: str


class AssignmentResponse(BaseModel):
    experiment_id: str
    user_id: str
    variant_id: str
    variant_name: str
    released: bool
