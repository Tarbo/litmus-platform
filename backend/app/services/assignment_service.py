from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.assignment import matches_targeting, unit_bucket
from app.models.assignment import Assignment
from app.models.experiment import Experiment, ExperimentStatus
from app.models.variant import Variant


class AssignmentService:
    @staticmethod
    def _control_variant(variants: list[Variant]) -> Variant:
        return next((variant for variant in variants if variant.key == 'control'), variants[0])

    @staticmethod
    def _weighted_variant(variants: list[Variant], bucket: float) -> Variant:
        total_weight = sum(max(0.0, variant.weight) for variant in variants)
        if total_weight <= 0:
            return AssignmentService._control_variant(variants)

        threshold = bucket * total_weight
        cumulative = 0.0
        chosen = variants[-1]
        for variant in variants:
            cumulative += max(0.0, variant.weight)
            if threshold <= cumulative:
                chosen = variant
                break
        return chosen

    @staticmethod
    def assign_unit(
        db: Session,
        experiment_id: str,
        unit_id: str,
        attributes: dict,
    ) -> tuple[Assignment, int]:
        experiment = db.scalar(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        if not experiment:
            raise HTTPException(status_code=404, detail='Experiment not found')
        if experiment.status != ExperimentStatus.RUNNING:
            raise HTTPException(status_code=400, detail='Experiment is not running')

        existing = db.scalar(
            select(Assignment).where(
                Assignment.experiment_id == experiment_id,
                Assignment.user_id == unit_id,
                Assignment.released_at.is_(None),
            )
        )
        if existing:
            return existing, experiment.version

        variants = db.scalars(
            select(Variant).where(Variant.experiment_id == experiment_id).order_by(Variant.created_at.asc())
        ).all()
        if not variants:
            raise HTTPException(status_code=400, detail='Experiment has no variants configured')

        control = AssignmentService._control_variant(variants)
        chosen = control

        targets_match = matches_targeting(experiment.targeting, attributes or {})
        if targets_match and experiment.ramp_pct > 0:
            ramp_bucket = unit_bucket(experiment_id, unit_id, experiment.assignment_salt, 'ramp')
            if ramp_bucket * 100 < experiment.ramp_pct:
                variant_bucket = unit_bucket(experiment_id, unit_id, experiment.assignment_salt, 'variant')
                chosen = AssignmentService._weighted_variant(variants, variant_bucket)

        assignment = Assignment(experiment_id=experiment_id, user_id=unit_id, variant_id=chosen.id)
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment, experiment.version

    @staticmethod
    def assign_user(db: Session, experiment_id: str, user_id: str) -> Assignment:
        assignment, _ = AssignmentService.assign_unit(
            db=db,
            experiment_id=experiment_id,
            unit_id=user_id,
            attributes={},
        )
        return assignment
