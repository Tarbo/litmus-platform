from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.experiment import ExperimentStatus
from app.schemas.variant import VariantCreate, VariantResponse


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    hypothesis: str = Field(min_length=5)
    mde: float = Field(default=0.05, gt=0, lt=1)
    baseline_rate: float = Field(default=0.1, gt=0, lt=1)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    power: float = Field(default=0.8, gt=0, lt=1)
    variants: list[VariantCreate]

    @model_validator(mode='after')
    def validate_allocations(self):
        total = sum(v.traffic_allocation for v in self.variants)
        if abs(total - 1.0) > 0.001:
            raise ValueError('Variant traffic_allocation values must sum to 1.0')
        if len(self.variants) < 2:
            raise ValueError('At least two variants are required')
        return self


class ExperimentResponse(BaseModel):
    id: str
    name: str
    hypothesis: str
    mde: float
    baseline_rate: float
    alpha: float
    power: float
    sample_size_required: int
    status: ExperimentStatus
    started_at: datetime | None
    ended_at: datetime | None
    termination_reason: str | None
    created_at: datetime
    updated_at: datetime
    variants: list[VariantResponse]

    model_config = {'from_attributes': True}


class ExperimentStatusUpdate(BaseModel):
    reason: str | None = None


class CondensedPerformance(BaseModel):
    experiment_id: str
    name: str
    status: ExperimentStatus
    exposures: int
    conversions: int
    conversion_rate: float
    uplift_vs_control: float
    confidence: float
    sample_progress: float


class ExecutiveSummary(BaseModel):
    passed: int
    failed: int
    running: int
    inconclusive: int
    terminated_without_cause: int


class ExperimentReport(BaseModel):
    experiment_id: str
    status: ExperimentStatus
    mde: float
    sample_size_required: int
    exposures: int
    conversions: int
    sample_progress: float
    control_conversion_rate: float
    treatment_conversion_rate: float
    uplift_vs_control: float
    uplift_ci_lower: float
    uplift_ci_upper: float
    p_value: float
    confidence: float
    recommendation: str
    guardrails_breached: int
    guardrails: list[dict]
    estimated_days_to_decision: int | None
    diff_in_diff_delta: float | None
    variant_performance: list[dict]
    last_updated_at: datetime
