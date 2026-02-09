from pydantic import BaseModel, Field


class VariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    traffic_allocation: float = Field(gt=0, le=1)


class VariantResponse(BaseModel):
    id: str
    name: str
    traffic_allocation: float

    model_config = {'from_attributes': True}
