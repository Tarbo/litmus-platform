import json

from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import EventCreate
from app.schemas.experiment import ExperimentCreate
from app.schemas.metric import GuardrailMetricCreate
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService
from app.services.metric_service import MetricService
from app.services.snapshot_service import SnapshotService


def test_auto_transition_to_failed_when_guardrail_breaches(tmp_path):
    db_path = tmp_path / 'litmus_m3.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Latency Guardrail Test',
                hypothesis='Variant increases conversion without harming latency',
                mde=0.05,
                baseline_rate=0.1,
                alpha=0.05,
                power=0.8,
                variants=[
                    {'name': 'control', 'traffic_allocation': 0.5},
                    {'name': 'treatment', 'traffic_allocation': 0.5},
                ],
            ),
        )
        experiment = ExperimentService.launch_experiment(db, experiment.id, ramp_pct=100)

        control_id = experiment.variants[0].id
        treatment_id = experiment.variants[1].id

        for i in range(800):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'c{i}', variant_id=control_id, event_type='exposure'))
        for i in range(100):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'cc{i}', variant_id=control_id, event_type='conversion'))
        for i in range(800):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f't{i}', variant_id=treatment_id, event_type='exposure'))
        for i in range(130):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'tc{i}', variant_id=treatment_id, event_type='conversion'))

        metric = MetricService.create_guardrail_metric(
            db,
            GuardrailMetricCreate(
                experiment_id=experiment.id,
                name='p95_latency_ms',
                value=460,
                threshold_value=350,
                direction='max',
            ),
        )
        assert metric.status.value == 'breached'

        report = ExperimentService.build_report(db, experiment)
        updated = ExperimentService.apply_outcome_transition(db, experiment, report)
        assert report['guardrails_breached'] == 1
        assert updated.status.value == 'failed'
    finally:
        db.close()
        engine.dispose()


def test_snapshot_persistence(tmp_path):
    db_path = tmp_path / 'litmus_m3_snapshot.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Snapshot Test',
                hypothesis='Snapshot records report history',
                mde=0.05,
                baseline_rate=0.1,
                alpha=0.05,
                power=0.8,
                variants=[
                    {'name': 'control', 'traffic_allocation': 0.5},
                    {'name': 'treatment', 'traffic_allocation': 0.5},
                ],
            ),
        )

        payload = {'sample_progress': 0.42, 'recommendation': 'continue_collecting'}
        snapshot = SnapshotService.create_snapshot(db, experiment.id, payload)
        items = SnapshotService.list_snapshots(db, experiment.id)

        assert snapshot.experiment_id == experiment.id
        assert len(items) == 1
        assert json.loads(items[0].snapshot_json)['sample_progress'] == 0.42
    finally:
        db.close()
        engine.dispose()
