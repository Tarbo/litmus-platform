from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decision_audit import DecisionAudit, DecisionSource
from app.models.experiment import Experiment, ExperimentStatus


class DecisionService:
    @staticmethod
    def record_decision(
        db: Session,
        experiment: Experiment,
        previous_status: ExperimentStatus,
        new_status: ExperimentStatus,
        reason: str | None,
        source: DecisionSource,
        actor: str,
    ) -> DecisionAudit:
        audit = DecisionAudit(
            experiment_id=experiment.id,
            previous_status=previous_status.value,
            new_status=new_status.value,
            reason=reason,
            source=source,
            actor=actor,
        )
        db.add(audit)
        db.flush()
        return audit

    @staticmethod
    def list_decisions(db: Session, experiment_id: str) -> list[DecisionAudit]:
        return db.scalars(
            select(DecisionAudit)
            .where(DecisionAudit.experiment_id == experiment_id)
            .order_by(DecisionAudit.created_at.desc())
        ).all()
