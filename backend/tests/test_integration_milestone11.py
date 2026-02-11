from fastapi import HTTPException

from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import EventCreate, ExposureEventCreate, MetricEventCreate
from app.schemas.experiment import ExperimentCreate
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService
from app.services.results_service import ResultsService


def _setup_running_experiment(db):
    experiment = ExperimentService.create_experiment(
        db,
        ExperimentCreate(
            name='M11 Results API',
            description='Validate exposure+metric ingestion and results output',
            owner_team='pricing-ds',
            created_by='m11.test',
            variants=[
                {'key': 'control', 'name': 'Control', 'weight': 0.5, 'config_json': {}},
                {'key': 'treatment', 'name': 'Treatment', 'weight': 0.5, 'config_json': {}},
            ],
            ramp_pct=100,
        ),
    )
    experiment = ExperimentService.launch_experiment(db, experiment.id, ramp_pct=100)
    variant_map = {variant.key: variant for variant in experiment.variants}
    return experiment, variant_map


def test_batch_ingestion_and_results_summary(tmp_path):
    db_path = tmp_path / 'm11_results.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment, variants = _setup_running_experiment(db)

        exposure_payloads = [
            ExposureEventCreate(
                experiment_id=experiment.id,
                unit_id=f'u-{idx}',
                variant_key='control' if idx < 4 else 'treatment',
            )
            for idx in range(8)
        ]
        assert EventService.ingest_exposure_batch(db, exposure_payloads) == 8

        metric_payloads = [
            MetricEventCreate(
                experiment_id=experiment.id,
                unit_id=f'm-{idx}',
                variant_key='control',
                metric_name='order_value',
                value=100 + idx,
            )
            for idx in range(3)
        ] + [
            MetricEventCreate(
                experiment_id=experiment.id,
                unit_id=f'mt-{idx}',
                variant_key='treatment',
                metric_name='order_value',
                value=130 + idx,
            )
            for idx in range(3)
        ]
        assert EventService.ingest_metric_batch(db, metric_payloads) == 6

        # Add conversion events to power lift estimates.
        for idx in range(2):
            EventService.ingest_event(
                db,
                EventCreate(
                    experiment_id=experiment.id,
                    user_id=f'c-{idx}',
                    variant_id=variants['control'].id,
                    event_type='conversion',
                    value=1,
                ),
            )
        for idx in range(3):
            EventService.ingest_event(
                db,
                EventCreate(
                    experiment_id=experiment.id,
                    user_id=f't-{idx}',
                    variant_id=variants['treatment'].id,
                    event_type='conversion',
                    value=1,
                ),
            )

        results = ResultsService.build_results(db=db, experiment_id=experiment.id, interval='hour')
        assert results['exposure_totals']['control'] == 4
        assert results['exposure_totals']['treatment'] == 4
        assert len(results['exposure_timeseries']) == 2
        assert len(results['metric_summaries']) == 2
        assert len(results['lift_estimates']) == 1
        assert results['lift_estimates'][0]['variant_key'] == 'treatment'
    finally:
        db.close()
        engine.dispose()


def test_results_interval_validation(tmp_path):
    db_path = tmp_path / 'm11_results_interval.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment, _ = _setup_running_experiment(db)
        try:
            ResultsService.build_results(db=db, experiment_id=experiment.id, interval='day')
            assert False, 'Expected invalid interval to fail'
        except HTTPException as exc:
            assert exc.status_code == 400
    finally:
        db.close()
        engine.dispose()
