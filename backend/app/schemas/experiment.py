from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.experiment import ExperimentStatus
from app.schemas.variant import VariantCreate, VariantResponse


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=5)
    hypothesis: str | None = Field(default=None, min_length=5)
    owner_team: str = Field(default='unknown-team', min_length=2, max_length=120)
    created_by: str = Field(default='system', min_length=2, max_length=120)
    tags: list[str] = Field(default_factory=list)
    unit_type: str = Field(default='user_id', min_length=2, max_length=80)
    targeting: dict = Field(default_factory=dict)
    ramp_pct: int = Field(default=0, ge=0, le=100)
    mde: float = Field(default=0.05, gt=0, lt=1)
    baseline_rate: float = Field(default=0.1, gt=0, lt=1)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    power: float = Field(default=0.8, gt=0, lt=1)
    variants: list[VariantCreate]

    @model_validator(mode='after')
    def validate_allocations(self):
        if self.description is None and self.hypothesis is not None:
            self.description = self.hypothesis
        if self.hypothesis is None and self.description is not None:
            self.hypothesis = self.description
        total = sum(v.weight or 0.0 for v in self.variants)
        if abs(total - 1.0) > 0.001:
            raise ValueError('Variant weights must sum to 1.0')
        if len(self.variants) < 2:
            raise ValueError('At least two variants are required')
        if self.description is None:
            raise ValueError('Description is required')
        return self


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: str
    hypothesis: str
    owner_team: str
    created_by: str
    tags: list[str]
    unit_type: str
    targeting: dict
    ramp_pct: int
    version: int
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


class ExperimentPatch(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=5)
    owner_team: str | None = Field(default=None, min_length=2, max_length=120)
    tags: list[str] | None = None
    targeting: dict | None = None
    ramp_pct: int | None = Field(default=None, ge=0, le=100)
    variants: list[VariantCreate] | None = None


class ExperimentLifecycleAction(BaseModel):
    ramp_pct: int | None = Field(default=None, ge=0, le=100)
    actor: str = Field(default='ui.operator', min_length=2, max_length=120)
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
    draft: int
    running: int
    paused: int
    stopped: int


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
    assignment_policy: str
    bandit_state: list[dict]
    last_updated_at: datetime
