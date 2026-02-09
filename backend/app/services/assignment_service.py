from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.assignment import deterministic_bucket
from app.models.assignment import Assignment
from app.models.experiment import Experiment, ExperimentStatus
from app.models.variant import Variant


class AssignmentService:
    @staticmethod
    def assign_user(db: Session, experiment_id: str, user_id: str) -> Assignment:
        experiment = db.scalar(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        if not experiment:
            raise HTTPException(status_code=404, detail='Experiment not found')
        if experiment.status != ExperimentStatus.running:
            raise HTTPException(status_code=400, detail='Experiment is not running')

        existing = db.scalar(
            select(Assignment).where(
                Assignment.experiment_id == experiment_id,
                Assignment.user_id == user_id,
                Assignment.released_at.is_(None),
            )
        )
        if existing:
            return existing

        variants = db.scalars(
            select(Variant).where(Variant.experiment_id == experiment_id).order_by(Variant.created_at.asc())
        ).all()
        if not variants:
            raise HTTPException(status_code=400, detail='Experiment has no variants configured')

        bucket = deterministic_bucket(f'{experiment_id}:{user_id}')
        cumulative = 0.0
        chosen = variants[0]
        for variant in variants:
            cumulative += variant.traffic_allocation
            if bucket <= cumulative:
                chosen = variant
                break

        assignment = Assignment(experiment_id=experiment_id, user_id=user_id, variant_id=chosen.id)
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
