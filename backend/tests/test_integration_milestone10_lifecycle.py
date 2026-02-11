from fastapi import HTTPException

from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.experiment import ExperimentCreate
from app.services.experiment_service import ExperimentService


def test_lifecycle_guards_launch_pause_stop(tmp_path):
    db_path = tmp_path / 'm10_lifecycle.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='M10 Lifecycle',
                description='Lifecycle transition coverage',
                owner_team='checkout-ds',
                created_by='m10.lifecycle',
                ramp_pct=0,
                variants=[
                    {'key': 'control', 'name': 'Control', 'weight': 0.5, 'config_json': {}},
                    {'key': 'treatment', 'name': 'Treatment', 'weight': 0.5, 'config_json': {}},
                ],
            ),
        )
        assert experiment.status.value == 'DRAFT'

        try:
            ExperimentService.pause_experiment(db, experiment.id)
            assert False, 'Expected pause on draft to fail'
        except HTTPException as exc:
            assert exc.status_code == 409

        try:
            ExperimentService.launch_experiment(db, experiment.id, ramp_pct=0)
            assert False, 'Expected launch with zero ramp to fail'
        except HTTPException as exc:
            assert exc.status_code == 422

        running = ExperimentService.launch_experiment(db, experiment.id, ramp_pct=10)
        assert running.status.value == 'RUNNING'
        assert running.ramp_pct == 10

        paused = ExperimentService.pause_experiment(db, experiment.id)
        assert paused.status.value == 'PAUSED'

        resumed = ExperimentService.launch_experiment(db, experiment.id, ramp_pct=30)
        assert resumed.status.value == 'RUNNING'
        assert resumed.ramp_pct == 30

        stopped = ExperimentService.stop_experiment(db, experiment.id, reason='kill switch')
        assert stopped.status.value == 'STOPPED'
        assert stopped.ramp_pct == 0

        try:
            ExperimentService.launch_experiment(db, experiment.id, ramp_pct=50)
            assert False, 'Expected relaunch after stop to fail'
        except HTTPException as exc:
            assert exc.status_code == 409
    finally:
        db.close()
        engine.dispose()
