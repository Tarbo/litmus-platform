from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import ExposureEventCreate, MetricEventCreate
from app.schemas.experiment import ExperimentCreate
from app.services.assignment_service import AssignmentService
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService
from app.services.results_service import ResultsService


def test_self_serve_lifecycle_smoke_flow(tmp_path):
    db_path = tmp_path / 'm14_smoke.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='M14 Smoke Flow',
                description='End-to-end smoke flow for self-serve lifecycle',
                owner_team='platform-smoke',
                created_by='m14.test',
                unit_type='user_id',
                targeting={'country': {'in': ['US', 'CA']}},
                ramp_pct=10,
                variants=[
                    {'key': 'control', 'name': 'Control', 'weight': 0.5, 'config_json': {'model': 'v1'}},
                    {'key': 'treatment', 'name': 'Treatment', 'weight': 0.5, 'config_json': {'model': 'v2'}},
                ],
            ),
        )
        assert experiment.status.value == 'DRAFT'

        experiment = ExperimentService.launch_experiment(db, experiment.id, ramp_pct=10)
        assert experiment.status.value == 'RUNNING'

        assignment, _ = AssignmentService.assign_unit(
            db=db,
            experiment_id=experiment.id,
            unit_id='smoke-unit-1',
            attributes={'country': 'US', 'segment': 'smoke'},
        )
        assert assignment.variant is not None

        variant_key = assignment.variant.key
        EventService.ingest_exposure(
            db,
            ExposureEventCreate(
                experiment_id=experiment.id,
                unit_id='smoke-unit-1',
                variant_key=variant_key,
                context={'source': 'm14-test'},
            ),
        )
        EventService.ingest_metric(
            db,
            MetricEventCreate(
                experiment_id=experiment.id,
                unit_id='smoke-unit-1',
                variant_key=variant_key,
                metric_name='order_value',
                value=123.45,
                context={'source': 'm14-test'},
            ),
        )

        results = ResultsService.build_results(db=db, experiment_id=experiment.id, interval='hour')
        assert results['experiment_id'] == experiment.id
        assert sum(results['exposure_totals'].values()) >= 1
        assert any(item['metric_name'] == 'order_value' for item in results['metric_summaries'])

        paused = ExperimentService.pause_experiment(db, experiment.id)
        assert paused.status.value == 'PAUSED'

        stopped = ExperimentService.stop_experiment(db, experiment.id, 'smoke complete')
        assert stopped.status.value == 'STOPPED'
    finally:
        db.close()
        engine.dispose()
