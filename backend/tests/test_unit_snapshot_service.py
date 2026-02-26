import json

from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.experiment import ExperimentCreate
from app.services.experiment_service import ExperimentService
from app.services.snapshot_service import SnapshotService


def test_create_snapshot_serializes_report_payload_with_enum_and_datetime(tmp_path):
    db_path = tmp_path / 'snapshot_test.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Snapshot Serialization',
                description='Report snapshot should serialize enum and datetime fields',
                variants=[
                    {'key': 'control', 'name': 'Control', 'weight': 0.5, 'config_json': {}},
                    {'key': 'treatment', 'name': 'Treatment', 'weight': 0.5, 'config_json': {}},
                ],
            ),
        )

        report = ExperimentService.build_report(db, ExperimentService.get_experiment(db, experiment.id))
        snapshot = SnapshotService.create_snapshot(db, experiment.id, report)

        payload = json.loads(snapshot.snapshot_json)
        assert payload['status'] == 'DRAFT'
        assert isinstance(payload['last_updated_at'], str)
    finally:
        db.close()
        engine.dispose()
