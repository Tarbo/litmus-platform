from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.experiment import ExperimentCreate, ExperimentPatch
from app.services.assignment_service import AssignmentService
from app.services.experiment_service import ExperimentService


def _create_and_launch(db):
    experiment = ExperimentService.create_experiment(
        db,
        ExperimentCreate(
            name='M10 Deterministic Assignment',
            description='Deterministic assignment test fixture',
            owner_team='pricing-ds',
            created_by='m10.test',
            unit_type='store_id',
            ramp_pct=100,
            targeting={'country': {'in': ['US', 'CA']}},
            variants=[
                {'key': 'control', 'name': 'Control', 'weight': 0.8, 'config_json': {'model': 'v1'}},
                {'key': 'treatment', 'name': 'Treatment', 'weight': 0.2, 'config_json': {'model': 'v2'}},
            ],
        ),
    )
    return ExperimentService.launch_experiment(db, experiment.id, ramp_pct=100)


def test_assignment_is_deterministic_for_same_unit(tmp_path):
    db_path = tmp_path / 'm10_deterministic.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = _create_and_launch(db)
        first, _ = AssignmentService.assign_unit(
            db=db, experiment_id=experiment.id, unit_id='store-123', attributes={'country': 'US'}
        )
        second, _ = AssignmentService.assign_unit(
            db=db, experiment_id=experiment.id, unit_id='store-123', attributes={'country': 'US'}
        )
        assert first.variant_id == second.variant_id
        assert first.id == second.id
    finally:
        db.close()
        engine.dispose()


def test_assignment_respects_ramp_and_targeting(tmp_path):
    db_path = tmp_path / 'm10_ramp_targeting.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = _create_and_launch(db)
        ExperimentService.patch_experiment(
            db,
            experiment.id,
            ExperimentPatch(ramp_pct=0),
        )
        ramp_zero_assignment, _ = AssignmentService.assign_unit(
            db=db, experiment_id=experiment.id, unit_id='store-ramp-zero', attributes={'country': 'US'}
        )
        assert ramp_zero_assignment.variant.key == 'control'

        ExperimentService.launch_experiment(db, experiment.id, ramp_pct=100)
        out_of_target_assignment, _ = AssignmentService.assign_unit(
            db=db, experiment_id=experiment.id, unit_id='store-out-target', attributes={'country': 'NG'}
        )
        assert out_of_target_assignment.variant.key == 'control'
    finally:
        db.close()
        engine.dispose()


def test_weight_distribution_is_sane(tmp_path):
    db_path = tmp_path / 'm10_distribution.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = _create_and_launch(db)
        counts = {'control': 0, 'treatment': 0}
        total = 2000
        for idx in range(total):
            assignment, _ = AssignmentService.assign_unit(
                db=db,
                experiment_id=experiment.id,
                unit_id=f'store-{idx}',
                attributes={'country': 'US'},
            )
            counts[assignment.variant.key] += 1

        treatment_share = counts['treatment'] / total
        assert 0.14 <= treatment_share <= 0.26
    finally:
        db.close()
        engine.dispose()
