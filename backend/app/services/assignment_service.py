import hashlib
import random

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.assignment import deterministic_bucket
from app.core.bandits import build_thompson_posteriors, choose_variant_thompson
from app.models.assignment import Assignment
from app.models.event import Event
from app.models.experiment import Experiment, ExperimentStatus
from app.models.variant import Variant


class AssignmentService:
    @staticmethod
    def _variant_event_counts(db: Session, experiment_id: str) -> dict[str, tuple[int, int]]:
        rows = db.execute(
            select(
                Event.variant_id,
                func.count(case((Event.event_type == 'exposure', 1))).label('exposures'),
                func.count(case((Event.event_type == 'conversion', 1))).label('conversions'),
            ).where(
                Event.experiment_id == experiment_id,
                Event.period == 'post',
                Event.variant_id.is_not(None),
            )
            .group_by(Event.variant_id)
        ).all()
        counts: dict[str, tuple[int, int]] = {}
        for variant_id, exposures, conversions in rows:
            if not variant_id:
                continue
            counts[variant_id] = (exposures or 0, conversions or 0)
        return counts

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

        variant_rows = [(variant.id, variant.name) for variant in variants]
        counts_by_variant = AssignmentService._variant_event_counts(db, experiment_id)

        # Deterministic user-scoped RNG gives reproducible assignments while still adapting to posterior updates.
        seed_input = f'{experiment_id}:{user_id}:{deterministic_bucket(f"{experiment_id}:{user_id}")}'
        seed = int(hashlib.sha256(seed_input.encode('utf-8')).hexdigest()[:16], 16)
        rng = random.Random(seed)

        posterior_choice = choose_variant_thompson(build_thompson_posteriors(variant_rows, counts_by_variant), rng)
        chosen = next((variant for variant in variants if variant.id == posterior_choice.variant_id), variants[0])

        assignment = Assignment(experiment_id=experiment_id, user_id=user_id, variant_id=chosen.id)
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
