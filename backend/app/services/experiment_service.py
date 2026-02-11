from datetime import datetime, timezone
import json
import random

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.statistics import (
    calculate_sample_size,
    confidence_from_p_value,
    diff_in_diff,
    two_proportion_z_test,
    uplift_confidence_interval,
)
from app.core.bandits import build_thompson_posteriors, estimate_win_probabilities
from app.models.assignment import Assignment
from app.models.decision_audit import DecisionSource
from app.models.event import Event
from app.models.experiment import Experiment, ExperimentStatus
from app.models.metric import GuardrailStatus, Metric
from app.models.variant import Variant
from app.services.decision_service import DecisionService
from app.schemas.experiment import ExperimentCreate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExperimentService:
    @staticmethod
    def serialize_experiment(experiment: Experiment) -> dict:
        variants = []
        for variant in experiment.variants:
            try:
                config_payload = json.loads(variant.config_json)
                if not isinstance(config_payload, dict):
                    config_payload = {}
            except json.JSONDecodeError:
                config_payload = {}
            variants.append(
                {
                    'id': variant.id,
                    'key': variant.key,
                    'name': variant.name,
                    'weight': variant.weight,
                    'traffic_allocation': variant.weight,
                    'config_json': config_payload,
                }
            )
        return {
            'id': experiment.id,
            'name': experiment.name,
            'description': experiment.description,
            'hypothesis': experiment.hypothesis,
            'owner_team': experiment.owner_team,
            'created_by': experiment.created_by,
            'tags': experiment.tags,
            'unit_type': experiment.unit_type,
            'targeting': experiment.targeting,
            'ramp_pct': experiment.ramp_pct,
            'version': experiment.version,
            'mde': experiment.mde,
            'baseline_rate': experiment.baseline_rate,
            'alpha': experiment.alpha,
            'power': experiment.power,
            'sample_size_required': experiment.sample_size_required,
            'status': experiment.status,
            'started_at': experiment.started_at,
            'ended_at': experiment.ended_at,
            'termination_reason': experiment.termination_reason,
            'created_at': experiment.created_at,
            'updated_at': experiment.updated_at,
            'variants': variants,
        }

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
    def create_experiment(db: Session, payload: ExperimentCreate) -> Experiment:
        sample_size = calculate_sample_size(payload.baseline_rate, payload.mde, payload.alpha, payload.power)
        experiment = Experiment(
            name=payload.name,
            description=payload.description or payload.hypothesis or '',
            hypothesis=payload.hypothesis,
            owner_team=payload.owner_team,
            created_by=payload.created_by,
            unit_type=payload.unit_type,
            tags_json=json.dumps(payload.tags),
            targeting_json=json.dumps(payload.targeting),
            ramp_pct=payload.ramp_pct,
            version=1,
            mde=payload.mde,
            baseline_rate=payload.baseline_rate,
            alpha=payload.alpha,
            power=payload.power,
            sample_size_required=sample_size,
            status=ExperimentStatus.DRAFT,
        )
        db.add(experiment)
        db.flush()

        variants = [
            Variant(
                experiment_id=experiment.id,
                key=variant.key or variant.name.lower().replace(' ', '_'),
                name=variant.name,
                weight=variant.weight or 0.0,
                config_json=variant.to_config_json(),
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
        return ExperimentService.stop_experiment(db, experiment_id, reason)

    @staticmethod
    def executive_summary(db: Session) -> dict[str, int]:
        rows = db.execute(select(Experiment.status, func.count(Experiment.id)).group_by(Experiment.status)).all()
        summary = {
            'draft': 0,
            'running': 0,
            'paused': 0,
            'stopped': 0,
        }
        for status, count in rows:
            summary[status.value.lower()] = count
        return summary

    @staticmethod
    def patch_experiment(db: Session, experiment_id: str, payload) -> Experiment:
        experiment = ExperimentService.get_experiment(db, experiment_id)
        if payload.name is not None:
            experiment.name = payload.name
        if payload.description is not None:
            experiment.description = payload.description
            experiment.hypothesis = payload.description
        if payload.owner_team is not None:
            experiment.owner_team = payload.owner_team
        if payload.tags is not None:
            experiment.tags_json = json.dumps(payload.tags)
        if payload.targeting is not None:
            experiment.targeting_json = json.dumps(payload.targeting)
        if payload.ramp_pct is not None:
            experiment.ramp_pct = payload.ramp_pct
        if payload.variants is not None:
            db.query(Variant).filter(Variant.experiment_id == experiment.id).delete(synchronize_session=False)
            db.add_all(
                [
                    Variant(
                        experiment_id=experiment.id,
                        key=variant.key or variant.name.lower().replace(' ', '_'),
                        name=variant.name,
                        weight=variant.weight or 0.0,
                        config_json=variant.to_config_json(),
                    )
                    for variant in payload.variants
                ]
            )
        experiment.version += 1
        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def launch_experiment(db: Session, experiment_id: str, ramp_pct: int | None) -> Experiment:
        experiment = ExperimentService.get_experiment(db, experiment_id)
        if experiment.status == ExperimentStatus.STOPPED:
            raise HTTPException(status_code=409, detail='Stopped experiment cannot be relaunched')
        if ramp_pct is not None:
            experiment.ramp_pct = ramp_pct
        if experiment.ramp_pct <= 0:
            raise HTTPException(status_code=422, detail='Launch requires ramp_pct greater than 0')
        if experiment.status != ExperimentStatus.RUNNING:
            experiment.status = ExperimentStatus.RUNNING
            experiment.started_at = utc_now()
            experiment.ended_at = None
            experiment.termination_reason = None
        experiment.version += 1
        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def pause_experiment(db: Session, experiment_id: str) -> Experiment:
        experiment = ExperimentService.get_experiment(db, experiment_id)
        if experiment.status == ExperimentStatus.STOPPED:
            raise HTTPException(status_code=409, detail='Stopped experiment cannot be paused')
        if experiment.status != ExperimentStatus.RUNNING:
            raise HTTPException(status_code=409, detail='Only running experiment can be paused')
        experiment.status = ExperimentStatus.PAUSED
        experiment.version += 1
        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def stop_experiment(db: Session, experiment_id: str, reason: str | None) -> Experiment:
        experiment = ExperimentService.get_experiment(db, experiment_id)
        if experiment.status == ExperimentStatus.STOPPED:
            return experiment
        experiment.status = ExperimentStatus.STOPPED
        experiment.ended_at = utc_now()
        experiment.termination_reason = reason or 'Stopped manually'
        experiment.ramp_pct = 0
        experiment.version += 1
        release_time = utc_now()
        db.query(Assignment).filter(
            Assignment.experiment_id == experiment_id,
            Assignment.released_at.is_(None),
        ).update({'released_at': release_time}, synchronize_session=False)
        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def _report_query(db: Session, experiment_id: str):
        return db.execute(
            select(
                func.count(case((Event.event_type == 'exposure', 1))).label('exposures'),
                func.count(case((Event.event_type == 'conversion', 1))).label('conversions'),
            ).where(Event.experiment_id == experiment_id, Event.period == 'post')
        ).one()

    @staticmethod
    def _variant_counts(db: Session, experiment_id: str, variant_id: str, period: str = 'post') -> tuple[int, int]:
        exposure = db.scalar(
            select(func.count(Event.id)).where(
                Event.experiment_id == experiment_id,
                Event.variant_id == variant_id,
                Event.event_type == 'exposure',
                Event.period == period,
            )
        )
        conversion = db.scalar(
            select(func.count(Event.id)).where(
                Event.experiment_id == experiment_id,
                Event.variant_id == variant_id,
                Event.event_type == 'conversion',
                Event.period == period,
            )
        )
        return exposure or 0, conversion or 0

    @staticmethod
    def build_report(db: Session, experiment: Experiment) -> dict:
        exposures, conversions = ExperimentService._report_query(db, experiment.id)
        sample_progress = min(1.0, exposures / experiment.sample_size_required) if experiment.sample_size_required else 0.0

        variants = experiment.variants
        variant_rows = [(variant.id, variant.name) for variant in variants]
        counts_by_variant = ExperimentService._variant_event_counts(db, experiment.id)
        posteriors = build_thompson_posteriors(variant_rows, counts_by_variant)
        win_probabilities = estimate_win_probabilities(
            posteriors=posteriors,
            rng=random.Random(experiment.id),
        )
        bandit_state = [
            {
                'variant_id': posterior.variant_id,
                'variant_name': posterior.variant_name,
                'exposures': posterior.exposures,
                'conversions': posterior.conversions,
                'alpha': round(posterior.alpha, 3),
                'beta': round(posterior.beta, 3),
                'expected_rate': round(posterior.expected_rate, 4),
                'win_probability': round(win_probabilities.get(posterior.variant_id, 0.0), 4),
            }
            for posterior in posteriors
        ]
        control_rate = 0.0
        treatment_rate = 0.0
        did_delta = None
        p_value = 1.0
        uplift_ci_lower = 0.0
        uplift_ci_upper = 0.0
        recommendation = 'continue_collecting'
        variant_performance = []
        guardrails = ExperimentService._latest_guardrails(db, experiment.id)
        guardrails_breached = sum(1 for g in guardrails if g['status'] == GuardrailStatus.breached.value)

        if variants:
            control = variants[0]
            control_post_exposure, control_post_conversion = ExperimentService._variant_counts(
                db, experiment.id, control.id, period='post'
            )
            control_pre_exposure, control_pre_conversion = ExperimentService._variant_counts(
                db, experiment.id, control.id, period='pre'
            )
            control_rate = (control_post_conversion / control_post_exposure) if control_post_exposure else 0.0
            control_pre_rate = (control_pre_conversion / control_pre_exposure) if control_pre_exposure else 0.0

            treatment_post_exposure = 0
            treatment_post_conversion = 0
            treatment_pre_exposure = 0
            treatment_pre_conversion = 0

            for variant in variants:
                post_exposure, post_conversion = ExperimentService._variant_counts(db, experiment.id, variant.id, period='post')
                pre_exposure, pre_conversion = ExperimentService._variant_counts(db, experiment.id, variant.id, period='pre')
                post_rate = (post_conversion / post_exposure) if post_exposure else 0.0
                pre_rate = (pre_conversion / pre_exposure) if pre_exposure else 0.0
                variant_performance.append(
                    {
                        'variant_id': variant.id,
                        'variant_name': variant.name,
                        'post_exposures': post_exposure,
                        'post_conversions': post_conversion,
                        'post_conversion_rate': round(post_rate, 4),
                        'pre_exposures': pre_exposure,
                        'pre_conversions': pre_conversion,
                        'pre_conversion_rate': round(pre_rate, 4),
                    }
                )
                if variant.id != control.id:
                    treatment_post_exposure += post_exposure
                    treatment_post_conversion += post_conversion
                    treatment_pre_exposure += pre_exposure
                    treatment_pre_conversion += pre_conversion

            treatment_rate = (treatment_post_conversion / treatment_post_exposure) if treatment_post_exposure else 0.0
            treatment_pre_rate = (treatment_pre_conversion / treatment_pre_exposure) if treatment_pre_exposure else 0.0

            uplift = treatment_rate - control_rate
            z_result = two_proportion_z_test(
                control_conversions=control_post_conversion,
                control_exposures=control_post_exposure,
                treatment_conversions=treatment_post_conversion,
                treatment_exposures=treatment_post_exposure,
            )
            p_value = z_result.p_value
            ci = uplift_confidence_interval(
                control_conversions=control_post_conversion,
                control_exposures=control_post_exposure,
                treatment_conversions=treatment_post_conversion,
                treatment_exposures=treatment_post_exposure,
            )
            uplift_ci_lower = ci.lower
            uplift_ci_upper = ci.upper

            if control_pre_exposure > 0 and treatment_pre_exposure > 0:
                did_delta = diff_in_diff(
                    pre_control_rate=control_pre_rate,
                    post_control_rate=control_rate,
                    pre_treatment_rate=treatment_pre_rate,
                    post_treatment_rate=treatment_rate,
                )

            if sample_progress < 1:
                recommendation = 'continue_collecting'
            elif guardrails_breached > 0:
                recommendation = 'fail'
            elif p_value <= experiment.alpha and uplift >= experiment.mde:
                recommendation = 'pass'
            elif p_value <= experiment.alpha and uplift < 0:
                recommendation = 'fail'
            else:
                recommendation = 'inconclusive'
        else:
            uplift = 0.0

        confidence = confidence_from_p_value(p_value)
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
            'uplift_ci_lower': round(uplift_ci_lower, 4),
            'uplift_ci_upper': round(uplift_ci_upper, 4),
            'p_value': round(p_value, 6),
            'confidence': confidence,
            'recommendation': recommendation,
            'guardrails_breached': guardrails_breached,
            'guardrails': guardrails,
            'estimated_days_to_decision': None if exposures == 0 else max(0, int((experiment.sample_size_required - exposures) / 200)),
            'diff_in_diff_delta': did_delta,
            'variant_performance': variant_performance,
            'assignment_policy': 'thompson_sampling',
            'bandit_state': bandit_state,
            'last_updated_at': utc_now(),
        }

    @staticmethod
    def _latest_guardrails(db: Session, experiment_id: str) -> list[dict]:
        metrics = db.scalars(
            select(Metric).where(Metric.experiment_id == experiment_id).order_by(Metric.observed_at.desc())
        ).all()
        latest_by_name: dict[str, Metric] = {}
        for metric in metrics:
            if metric.name not in latest_by_name:
                latest_by_name[metric.name] = metric
        return [
            {
                'name': metric.name,
                'value': metric.value,
                'threshold_value': metric.threshold_value,
                'direction': metric.direction.value,
                'status': metric.status.value,
                'observed_at': metric.observed_at.isoformat(),
            }
            for metric in latest_by_name.values()
        ]

    @staticmethod
    def apply_outcome_transition(db: Session, experiment: Experiment, report: dict) -> Experiment:
        if experiment.status != ExperimentStatus.running:
            return experiment
        if report['sample_progress'] < 1:
            return experiment

        previous_status = experiment.status
        recommendation = report['recommendation']
        if recommendation == 'pass':
            experiment.status = ExperimentStatus.passed
        elif recommendation == 'fail':
            experiment.status = ExperimentStatus.failed
        else:
            experiment.status = ExperimentStatus.inconclusive
        experiment.ended_at = utc_now()
        DecisionService.record_decision(
            db=db,
            experiment=experiment,
            previous_status=previous_status,
            new_status=experiment.status,
            reason=f'Auto transition from recommendation={recommendation}',
            source=DecisionSource.auto,
            actor='system',
        )
        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def override_status(
        db: Session,
        experiment_id: str,
        new_status: ExperimentStatus,
        reason: str | None,
        actor: str,
    ) -> Experiment:
        experiment = ExperimentService.get_experiment(db, experiment_id)
        previous_status = experiment.status
        if previous_status == new_status:
            return experiment

        experiment.status = new_status
        if new_status != ExperimentStatus.running:
            experiment.ended_at = utc_now()
        DecisionService.record_decision(
            db=db,
            experiment=experiment,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            source=DecisionSource.manual,
            actor=actor,
        )
        db.commit()
        db.refresh(experiment)
        return experiment

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

    @staticmethod
    def export_report_payload(report: dict, fmt: str) -> str:
        if fmt == 'json':
            import json

            serializable = dict(report)
            serializable['status'] = report['status'].value if hasattr(report['status'], 'value') else report['status']
            serializable['last_updated_at'] = (
                report['last_updated_at'].isoformat()
                if hasattr(report['last_updated_at'], 'isoformat')
                else report['last_updated_at']
            )
            return json.dumps(serializable, indent=2)

        if fmt == 'csv':
            headers = [
                'experiment_id',
                'status',
                'recommendation',
                'sample_progress',
                'confidence',
                'p_value',
                'uplift_vs_control',
                'guardrails_breached',
            ]
            values = [
                str(report['experiment_id']),
                str(report['status'].value if hasattr(report['status'], 'value') else report['status']),
                str(report['recommendation']),
                str(report['sample_progress']),
                str(report['confidence']),
                str(report['p_value']),
                str(report['uplift_vs_control']),
                str(report['guardrails_breached']),
            ]
            return ','.join(headers) + '\n' + ','.join(values) + '\n'

        raise HTTPException(status_code=400, detail='format must be one of: json, csv')
