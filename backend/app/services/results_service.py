from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.statistics import two_proportion_z_test, uplift_confidence_interval
from app.models.event import Event
from app.models.experiment import Experiment
from app.models.variant import Variant


class ResultsService:
    @staticmethod
    def _bucket_start(ts: datetime, interval: str) -> datetime:
        ts_utc = ts.astimezone(timezone.utc)
        if interval == 'minute':
            return ts_utc.replace(second=0, microsecond=0)
        return ts_utc.replace(minute=0, second=0, microsecond=0)

    @staticmethod
    def build_results(db: Session, experiment_id: str, interval: str = 'hour') -> dict:
        if interval not in {'minute', 'hour'}:
            raise HTTPException(status_code=400, detail='interval must be minute or hour')

        experiment = db.scalar(
            select(Experiment).where(Experiment.id == experiment_id).options(selectinload(Experiment.variants))
        )
        if experiment is None:
            raise HTTPException(status_code=404, detail='Experiment not found')

        variants = db.scalars(
            select(Variant).where(Variant.experiment_id == experiment_id).order_by(Variant.created_at.asc())
        ).all()
        if not variants:
            raise HTTPException(status_code=400, detail='Experiment has no variants configured')

        variant_by_id = {variant.id: variant for variant in variants}
        control = next((variant for variant in variants if variant.key == 'control'), variants[0])

        events = db.scalars(
            select(Event).where(Event.experiment_id == experiment_id).order_by(Event.observed_at.asc())
        ).all()

        exposures_by_variant: dict[str, int] = defaultdict(int)
        conversions_by_variant: dict[str, int] = defaultdict(int)
        exposure_points: dict[str, dict[datetime, int]] = defaultdict(lambda: defaultdict(int))
        metric_accumulator: dict[tuple[str, str], list[float]] = defaultdict(list)

        for event in events:
            if event.variant_id is None or event.variant_id not in variant_by_id:
                continue
            variant = variant_by_id[event.variant_id]
            timestamp = event.observed_at or event.created_at
            if event.event_type == 'exposure':
                exposures_by_variant[variant.key] += 1
                exposure_points[variant.key][ResultsService._bucket_start(timestamp, interval)] += 1
            elif event.event_type == 'conversion':
                conversions_by_variant[variant.key] += 1
            elif event.event_type == 'metric' and event.metric_name:
                metric_accumulator[(variant.key, event.metric_name)].append(float(event.value))

        exposure_timeseries = []
        for variant in variants:
            series = exposure_points.get(variant.key, {})
            points = [
                {
                    'bucket_start': bucket_start,
                    'exposures': count,
                }
                for bucket_start, count in sorted(series.items(), key=lambda item: item[0])
            ]
            exposure_timeseries.append(
                {
                    'variant_key': variant.key,
                    'variant_name': variant.name,
                    'points': points,
                }
            )

        metric_summaries = []
        for (variant_key, metric_name), values in sorted(metric_accumulator.items(), key=lambda item: item[0]):
            variant = next((item for item in variants if item.key == variant_key), None)
            if variant is None:
                continue
            metric_summaries.append(
                {
                    'variant_key': variant_key,
                    'variant_name': variant.name,
                    'metric_name': metric_name,
                    'count': len(values),
                    'mean': round(sum(values) / len(values), 6),
                }
            )

        lift_estimates = []
        control_exposures = exposures_by_variant.get(control.key, 0)
        control_conversions = conversions_by_variant.get(control.key, 0)
        control_rate = (control_conversions / control_exposures) if control_exposures else 0.0

        for variant in variants:
            if variant.id == control.id:
                continue
            treatment_exposures = exposures_by_variant.get(variant.key, 0)
            treatment_conversions = conversions_by_variant.get(variant.key, 0)
            treatment_rate = (treatment_conversions / treatment_exposures) if treatment_exposures else 0.0
            if control_exposures == 0 or treatment_exposures == 0:
                p_value = 1.0
                ci_lower = 0.0
                ci_upper = 0.0
            else:
                z_result = two_proportion_z_test(
                    control_conversions=control_conversions,
                    control_exposures=control_exposures,
                    treatment_conversions=treatment_conversions,
                    treatment_exposures=treatment_exposures,
                )
                ci = uplift_confidence_interval(
                    control_conversions=control_conversions,
                    control_exposures=control_exposures,
                    treatment_conversions=treatment_conversions,
                    treatment_exposures=treatment_exposures,
                )
                p_value = z_result.p_value
                ci_lower = ci.lower
                ci_upper = ci.upper

            lift_estimates.append(
                {
                    'variant_key': variant.key,
                    'variant_name': variant.name,
                    'control_rate': round(control_rate, 6),
                    'treatment_rate': round(treatment_rate, 6),
                    'absolute_lift': round(treatment_rate - control_rate, 6),
                    'ci_lower': round(ci_lower, 6),
                    'ci_upper': round(ci_upper, 6),
                    'p_value': round(p_value, 6),
                }
            )

        return {
            'experiment_id': experiment_id,
            'generated_at': datetime.now(timezone.utc),
            'exposure_totals': {variant.key: exposures_by_variant.get(variant.key, 0) for variant in variants},
            'exposure_timeseries': exposure_timeseries,
            'metric_summaries': metric_summaries,
            'lift_estimates': lift_estimates,
        }
