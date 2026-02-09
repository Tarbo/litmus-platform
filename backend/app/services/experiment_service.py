from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.statistics import approximate_confidence, calculate_sample_size
from app.models.assignment import Assignment
from app.models.event import Event
from app.models.experiment import Experiment, ExperimentStatus
from app.models.variant import Variant
from app.schemas.experiment import ExperimentCreate


class ExperimentService:
    @staticmethod
    def create_experiment(db: Session, payload: ExperimentCreate) -> Experiment:
        sample_size = calculate_sample_size(payload.baseline_rate, payload.mde, payload.alpha, payload.power)
        experiment = Experiment(
            name=payload.name,
            hypothesis=payload.hypothesis,
            mde=payload.mde,
            baseline_rate=payload.baseline_rate,
            alpha=payload.alpha,
            power=payload.power,
            sample_size_required=sample_size,
            status=ExperimentStatus.running,
            started_at=datetime.utcnow(),
        )
        db.add(experiment)
        db.flush()

        variants = [
            Variant(
                experiment_id=experiment.id,
                name=variant.name,
                traffic_allocation=variant.traffic_allocation,
            )
            for variant in payload.variants
        ]
        db.add_all(variants)
        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def list_experiments(db: Session) -> list[Experiment]:
        return db.scalars(select(Experiment).options(selectinload(Experiment.variants)).order_by(Experiment.created_at.desc())).all()

    @staticmethod
    def get_experiment(db: Session, experiment_id: str) -> Experiment:
        experiment = db.scalar(
            select(Experiment).where(Experiment.id == experiment_id).options(selectinload(Experiment.variants))
        )
        if not experiment:
            raise HTTPException(status_code=404, detail='Experiment not found')
        return experiment

    @staticmethod
    def terminate_experiment(db: Session, experiment_id: str, reason: str | None) -> Experiment:
        experiment = ExperimentService.get_experiment(db, experiment_id)
        if experiment.status != ExperimentStatus.running:
            raise HTTPException(status_code=400, detail='Only running experiments can be terminated')

        experiment.status = ExperimentStatus.terminated_without_cause
        experiment.termination_reason = reason or 'Terminated manually from UI'
        experiment.ended_at = datetime.utcnow()

        release_time = datetime.utcnow()
        db.query(Assignment).filter(
            Assignment.experiment_id == experiment_id,
            Assignment.released_at.is_(None),
        ).update({'released_at': release_time}, synchronize_session=False)

        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def executive_summary(db: Session) -> dict[str, int]:
        rows = db.execute(select(Experiment.status, func.count(Experiment.id)).group_by(Experiment.status)).all()
        summary = {
            'passed': 0,
            'failed': 0,
            'running': 0,
            'inconclusive': 0,
            'terminated_without_cause': 0,
        }
        for status, count in rows:
            summary[status.value] = count
        return summary

    @staticmethod
    def _report_query(db: Session, experiment_id: str):
        return db.execute(
            select(
                func.count(case((Event.event_type == 'exposure', 1))).label('exposures'),
                func.count(case((Event.event_type == 'conversion', 1))).label('conversions'),
            ).where(Event.experiment_id == experiment_id)
        ).one()

    @staticmethod
    def _variant_conversion_rate(db: Session, experiment_id: str, variant_id: str) -> float:
        exposure = db.scalar(
            select(func.count(Event.id)).where(
                Event.experiment_id == experiment_id,
                Event.variant_id == variant_id,
                Event.event_type == 'exposure',
            )
        )
        conversion = db.scalar(
            select(func.count(Event.id)).where(
                Event.experiment_id == experiment_id,
                Event.variant_id == variant_id,
                Event.event_type == 'conversion',
            )
        )
        if not exposure:
            return 0.0
        return conversion / exposure

    @staticmethod
    def build_report(db: Session, experiment: Experiment) -> dict:
        exposures, conversions = ExperimentService._report_query(db, experiment.id)
        sample_progress = min(1.0, exposures / experiment.sample_size_required) if experiment.sample_size_required else 0.0

        variants = experiment.variants
        control_rate = 0.0
        treatment_rate = 0.0
        if variants:
            control_rate = ExperimentService._variant_conversion_rate(db, experiment.id, variants[0].id)
            if len(variants) > 1:
                treatment_rates = [ExperimentService._variant_conversion_rate(db, experiment.id, v.id) for v in variants[1:]]
                treatment_rate = sum(treatment_rates) / len(treatment_rates)

        uplift = treatment_rate - control_rate
        confidence = approximate_confidence(exposures, conversions, experiment.mde)
        return {
            'experiment_id': experiment.id,
            'status': experiment.status,
            'mde': experiment.mde,
            'sample_size_required': experiment.sample_size_required,
            'exposures': exposures,
            'conversions': conversions,
            'sample_progress': round(sample_progress, 4),
            'control_conversion_rate': round(control_rate, 4),
            'treatment_conversion_rate': round(treatment_rate, 4),
            'uplift_vs_control': round(uplift, 4),
            'confidence': confidence,
            'estimated_days_to_decision': None if exposures == 0 else max(0, int((experiment.sample_size_required - exposures) / 200)),
            'diff_in_diff_delta': None,
            'last_updated_at': datetime.utcnow(),
        }

    @staticmethod
    def condensed_running_reports(db: Session):
        experiments = db.scalars(
            select(Experiment)
            .where(Experiment.status == ExperimentStatus.running)
            .options(selectinload(Experiment.variants))
            .order_by(Experiment.created_at.desc())
        ).all()
        cards = []
        for exp in experiments:
            report = ExperimentService.build_report(db, exp)
            cards.append(
                {
                    'experiment_id': exp.id,
                    'name': exp.name,
                    'status': exp.status,
                    'exposures': report['exposures'],
                    'conversions': report['conversions'],
                    'conversion_rate': round((report['conversions'] / report['exposures']), 4)
                    if report['exposures']
                    else 0.0,
                    'uplift_vs_control': report['uplift_vs_control'],
                    'confidence': report['confidence'],
                    'sample_progress': report['sample_progress'],
                }
            )
        return cards
