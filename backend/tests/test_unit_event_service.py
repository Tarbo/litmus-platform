from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import EventCreate
from app.schemas.experiment import ExperimentCreate
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService


def test_serialize_event_returns_context_json_dict(tmp_path):
    db_path = tmp_path / 'event_service.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Event Serialization',
                description='Event responses should emit context_json as an object',
                variants=[
                    {'key': 'control', 'name': 'Control', 'weight': 0.5, 'config_json': {}},
                    {'key': 'treatment', 'name': 'Treatment', 'weight': 0.5, 'config_json': {}},
                ],
            ),
        )
        variant_id = experiment.variants[0].id
        event = EventService.ingest_event(
            db,
            EventCreate(
                experiment_id=experiment.id,
                user_id='unit-1',
                variant_id=variant_id,
                event_type='conversion',
                context_json={'source': 'unit-test'},
            ),
        )
        payload = EventService.serialize_event(event)
        assert isinstance(payload['context_json'], dict)
        assert payload['context_json']['source'] == 'unit-test'
    finally:
        db.close()
        engine.dispose()
