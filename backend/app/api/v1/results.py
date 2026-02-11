from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.results import ExperimentResultsResponse
from app.services.results_service import ResultsService

router = APIRouter(prefix='/results', tags=['results'])


@router.get('/{experiment_id}', response_model=ExperimentResultsResponse)
def get_results(
    experiment_id: str,
    interval: str = Query(default='hour'),
    db: Session = Depends(get_db),
):
    return ResultsService.build_results(db=db, experiment_id=experiment_id, interval=interval)
