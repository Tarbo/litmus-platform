import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.experiment import (
    CondensedPerformance,
    ExecutiveSummary,
    ExperimentCreate,
    ExperimentReport,
    ExperimentResponse,
    ExperimentStatusUpdate,
)
from app.schemas.snapshot import ReportSnapshotResponse
from app.services.experiment_service import ExperimentService
from app.services.snapshot_service import SnapshotService

router = APIRouter(prefix='/experiments', tags=['experiments'])


@router.post('', response_model=ExperimentResponse)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)):
    return ExperimentService.create_experiment(db, payload)


@router.get('', response_model=list[ExperimentResponse])
def list_experiments(db: Session = Depends(get_db)):
    return ExperimentService.list_experiments(db)


@router.get('/running', response_model=list[CondensedPerformance])
def running_experiments(db: Session = Depends(get_db)):
    return ExperimentService.condensed_running_reports(db)


@router.get('/executive-summary', response_model=ExecutiveSummary)
def executive_summary(db: Session = Depends(get_db)):
    return ExperimentService.executive_summary(db)


@router.get('/{experiment_id}', response_model=ExperimentResponse)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    return ExperimentService.get_experiment(db, experiment_id)


@router.post('/{experiment_id}/terminate', response_model=ExperimentResponse)
def terminate_experiment(experiment_id: str, payload: ExperimentStatusUpdate, db: Session = Depends(get_db)):
    return ExperimentService.terminate_experiment(db, experiment_id, payload.reason)


@router.get('/{experiment_id}/report', response_model=ExperimentReport)
def experiment_report(experiment_id: str, db: Session = Depends(get_db)):
    experiment = ExperimentService.get_experiment(db, experiment_id)
    report = ExperimentService.build_report(db, experiment)
    experiment = ExperimentService.apply_outcome_transition(db, experiment, report)
    report['status'] = experiment.status
    SnapshotService.create_snapshot(db, experiment_id, report)
    return report


@router.get('/{experiment_id}/snapshots', response_model=list[ReportSnapshotResponse])
def experiment_snapshots(experiment_id: str, db: Session = Depends(get_db)):
    snapshots = SnapshotService.list_snapshots(db, experiment_id)
    return [
        ReportSnapshotResponse(
            id=snapshot.id,
            experiment_id=snapshot.experiment_id,
            snapshot=json.loads(snapshot.snapshot_json),
            created_at=snapshot.created_at,
        )
        for snapshot in snapshots
    ]
