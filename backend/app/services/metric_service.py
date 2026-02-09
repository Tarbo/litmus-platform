from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.metric import GuardrailDirection, GuardrailStatus, Metric
from app.schemas.metric import GuardrailMetricCreate


class MetricService:
    @staticmethod
    def create_guardrail_metric(db: Session, payload: GuardrailMetricCreate) -> Metric:
        breached = False
        if payload.direction == GuardrailDirection.max:
            breached = payload.value > payload.threshold_value
        elif payload.direction == GuardrailDirection.min:
            breached = payload.value < payload.threshold_value

        metric = Metric(
            experiment_id=payload.experiment_id,
            name=payload.name,
            value=payload.value,
            threshold_value=payload.threshold_value,
            direction=payload.direction,
            status=GuardrailStatus.breached if breached else GuardrailStatus.healthy,
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric

    @staticmethod
    def list_guardrails_for_experiment(db: Session, experiment_id: str) -> list[Metric]:
        return db.scalars(
            select(Metric).where(Metric.experiment_id == experiment_id).order_by(Metric.observed_at.desc())
        ).all()
