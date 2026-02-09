from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.experiment import ExperimentCreate
from app.services.experiment_service import ExperimentService


def test_executive_summary_includes_running_and_terminated(tmp_path):
    db_path = tmp_path / 'litmus_summary.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        payload = ExperimentCreate(
            name='Summary Test',
            hypothesis='Summary counts status buckets',
            mde=0.05,
            baseline_rate=0.1,
            alpha=0.05,
            power=0.8,
            variants=[
                {'name': 'control', 'traffic_allocation': 0.5},
                {'name': 'treatment', 'traffic_allocation': 0.5},
            ],
        )
        experiment = ExperimentService.create_experiment(db, payload)

        summary_running = ExperimentService.executive_summary(db)
        assert summary_running['running'] == 1

        ExperimentService.terminate_experiment(db, experiment.id, 'summary termination')
        summary_terminated = ExperimentService.executive_summary(db)
        assert summary_terminated['terminated_without_cause'] == 1
    finally:
        db.close()
        engine.dispose()
