from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import EventCreate
from app.schemas.experiment import ExperimentCreate
from app.models.experiment import ExperimentStatus
from app.services.decision_service import DecisionService
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService


def test_manual_decision_override_records_audit(tmp_path):
    db_path = tmp_path / 'litmus_m4_manual.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Manual Override Test',
                hypothesis='Operator can finalize experiment decision manually',
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

        updated = ExperimentService.override_status(
            db=db,
            experiment_id=experiment.id,
            new_status=ExperimentStatus.inconclusive,
            reason='manual close by operator',
            actor='ops.user',
        )

        assert updated.status.value == 'inconclusive'
        decisions = DecisionService.list_decisions(db, experiment.id)
        assert len(decisions) == 1
        assert decisions[0].source.value == 'manual'
        assert decisions[0].actor == 'ops.user'
    finally:
        db.close()
        engine.dispose()


def test_auto_decision_records_audit(tmp_path):
    db_path = tmp_path / 'litmus_m4_auto.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Auto Decision Test',
                hypothesis='Auto transition should write decision history',
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
        for i in range(1000):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'c{i}', variant_id=control_id, event_type='exposure'))
        for i in range(50):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'cc{i}', variant_id=control_id, event_type='conversion'))
        for i in range(1000):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f't{i}', variant_id=treatment_id, event_type='exposure'))
        for i in range(160):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'tc{i}', variant_id=treatment_id, event_type='conversion'))

        report = ExperimentService.build_report(db, experiment)
        updated = ExperimentService.apply_outcome_transition(db, experiment, report)
        decisions = DecisionService.list_decisions(db, experiment.id)

        assert updated.status.value in {'passed', 'inconclusive', 'failed'}
        assert len(decisions) == 1
        assert decisions[0].source.value == 'auto'
    finally:
        db.close()
        engine.dispose()
