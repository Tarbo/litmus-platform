from datetime import datetime

from pydantic import BaseModel


class ExposureSeriesPoint(BaseModel):
    bucket_start: datetime
    exposures: int


class ExposureSeriesByVariant(BaseModel):
    variant_key: str
    variant_name: str
    points: list[ExposureSeriesPoint]


class MetricSummaryByVariant(BaseModel):
    variant_key: str
    variant_name: str
    metric_name: str
    count: int
    mean: float


class LiftEstimate(BaseModel):
    variant_key: str
    variant_name: str
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    ci_lower: float
    ci_upper: float
    p_value: float


class ExperimentResultsResponse(BaseModel):
    experiment_id: str
    generated_at: datetime
    exposure_totals: dict[str, int]
    exposure_timeseries: list[ExposureSeriesByVariant]
    metric_summaries: list[MetricSummaryByVariant]
    lift_estimates: list[LiftEstimate]
