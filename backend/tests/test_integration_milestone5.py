from fastapi import HTTPException

from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.schemas.event import EventCreate
from app.schemas.experiment import ExperimentCreate
from app.services.event_service import EventService
from app.services.experiment_service import ExperimentService


def test_report_export_formats(tmp_path):
    db_path = tmp_path / 'litmus_m5_export.db'
    session_maker, engine = build_sessionmaker(f'sqlite:///{db_path}')
    init_db(engine)

    db = session_maker()
    try:
        experiment = ExperimentService.create_experiment(
            db,
            ExperimentCreate(
                name='Export Test',
                hypothesis='Reports can export to json and csv',
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

        control_id = experiment.variants[0].id
        for i in range(20):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'u{i}', variant_id=control_id, event_type='exposure'))
        for i in range(2):
            EventService.ingest_event(db, EventCreate(experiment_id=experiment.id, user_id=f'c{i}', variant_id=control_id, event_type='conversion'))

        report = ExperimentService.build_report(db, experiment)
        as_json = ExperimentService.export_report_payload(report, 'json')
        as_csv = ExperimentService.export_report_payload(report, 'csv')

        assert '"experiment_id"' in as_json
        assert 'experiment_id,status,recommendation' in as_csv

        try:
            ExperimentService.export_report_payload(report, 'xml')
            assert False, 'Expected invalid export format to fail'
        except HTTPException as exc:
            assert exc.status_code == 400
    finally:
        db.close()
        engine.dispose()
