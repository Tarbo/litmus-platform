from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import EventCreate
from app.schemas.experiment import ExperimentCreate
from app.services.assignment_service import AssignmentService
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService


def test_thompson_sampling_favors_variant_with_stronger_conversion_signal(tmp_path):
    db_path = tmp_path / 'litmus_bandit.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Bandit policy test',
                hypothesis='Thompson sampling shifts traffic to the best variant',
                variants=[
                    {'name': 'control', 'traffic_allocation': 0.5},
                    {'name': 'treatment', 'traffic_allocation': 0.5},
                ],
            ),
        )
        experiment = ExperimentService.get_experiment(db, experiment.id)
        variant_ids = {variant.name: variant.id for variant in experiment.variants}

        for idx in range(80):
            EventService.ingest_event(
                db,
                EventCreate(
                    experiment_id=experiment.id,
                    user_id=f'seed-c-{idx}',
                    variant_id=variant_ids['control'],
                    event_type='exposure',
                ),
            )
            EventService.ingest_event(
                db,
                EventCreate(
                    experiment_id=experiment.id,
                    user_id=f'seed-t-{idx}',
                    variant_id=variant_ids['treatment'],
                    event_type='exposure',
                ),
            )
            if idx < 12:
                EventService.ingest_event(
                    db,
                    EventCreate(
                        experiment_id=experiment.id,
                        user_id=f'seed-c-{idx}',
                        variant_id=variant_ids['control'],
                        event_type='conversion',
                    ),
                )
            if idx < 48:
                EventService.ingest_event(
                    db,
                    EventCreate(
                        experiment_id=experiment.id,
                        user_id=f'seed-t-{idx}',
                        variant_id=variant_ids['treatment'],
                        event_type='conversion',
                    ),
                )

        assigned = {'control': 0, 'treatment': 0}
        for idx in range(200):
            assignment = AssignmentService.assign_user(db, experiment.id, f'new-{idx}')
            if assignment.variant_id == variant_ids['control']:
                assigned['control'] += 1
            else:
                assigned['treatment'] += 1

        treatment_share = assigned['treatment'] / 200
        assert treatment_share > 0.65
    finally:
        db.close()
        engine.dispose()


def test_report_includes_bandit_state_metadata(tmp_path):
    db_path = tmp_path / 'litmus_bandit_report.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Bandit report metadata',
                hypothesis='Report includes Thompson posterior diagnostics',
                variants=[
                    {'name': 'control', 'traffic_allocation': 0.5},
                    {'name': 'treatment', 'traffic_allocation': 0.5},
                ],
            ),
        )
        report = ExperimentService.build_report(db, ExperimentService.get_experiment(db, experiment.id))

        assert report['assignment_policy'] == 'thompson_sampling'
        assert len(report['bandit_state']) == 2
        assert {'variant_id', 'variant_name', 'alpha', 'beta', 'expected_rate', 'win_probability'}.issubset(
            set(report['bandit_state'][0].keys())
        )
    finally:
        db.close()
        engine.dispose()
