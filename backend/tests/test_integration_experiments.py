from fastapi import HTTPException

from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import EventCreate
from app.schemas.experiment import ExperimentCreate
from app.services.assignment_service import AssignmentService
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService


def test_experiment_lifecycle_terminate_releases_assignments(tmp_path):
    db_path = tmp_path / 'litmus_test.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        create_payload = ExperimentCreate(
            name='Checkout CTA Test',
            hypothesis='Green button improves paid checkout conversion',
            mde=0.05,
            baseline_rate=0.1,
            alpha=0.05,
            power=0.8,
            variants=[
                {'name': 'control', 'traffic_allocation': 0.5},
                {'name': 'treatment', 'traffic_allocation': 0.5},
            ],
        )
        experiment = ExperimentService.create_experiment(db, create_payload)
        experiment = ExperimentService.launch_experiment(db, experiment.id, ramp_pct=100)

        assignment = AssignmentService.assign_user(db, experiment.id, 'u-1')

        EventService.ingest_event(
            db,
            EventCreate(
                experiment_id=experiment.id,
                user_id='u-1',
                variant_id=assignment.variant_id,
                event_type='exposure',
                value=1,
            ),
        )
        EventService.ingest_event(
            db,
            EventCreate(
                experiment_id=experiment.id,
                user_id='u-1',
                variant_id=assignment.variant_id,
                event_type='conversion',
                value=1,
            ),
        )
        EventService.ingest_event(
            db,
            EventCreate(
                experiment_id=experiment.id,
                user_id='u-1',
                variant_id=assignment.variant_id,
                event_type='exposure',
                period='pre',
                value=1,
            ),
        )
        EventService.ingest_event(
            db,
            EventCreate(
                experiment_id=experiment.id,
                user_id='u-1',
                variant_id=assignment.variant_id,
                event_type='conversion',
                period='pre',
                value=1,
            ),
        )

        report = ExperimentService.build_report(db, ExperimentService.get_experiment(db, experiment.id))
        assert report['exposures'] == 1
        assert report['conversions'] == 1
        assert 'p_value' in report
        assert 'variant_performance' in report

        terminated = ExperimentService.terminate_experiment(db, experiment.id, 'manual stop from operations')
        assert terminated.status.value == 'terminated_without_cause'

        try:
            AssignmentService.assign_user(db, experiment.id, 'u-2')
            assert False, 'Expected assigning on terminated experiment to fail'
        except HTTPException as exc:
            assert exc.status_code == 400
    finally:
        db.close()
        engine.dispose()
