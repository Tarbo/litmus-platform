from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_write_access
from app.schemas.metric import GuardrailMetricCreate, GuardrailMetricResponse
from app.services.metric_service import MetricService

router = APIRouter(prefix='/metrics', tags=['metrics'])


@router.post('/guardrails', response_model=GuardrailMetricResponse)
def create_guardrail_metric(
    payload: GuardrailMetricCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    return MetricService.create_guardrail_metric(db, payload)


@router.get('/guardrails/{experiment_id}', response_model=list[GuardrailMetricResponse])
def list_guardrails(experiment_id: str, db: Session = Depends(get_db)):
    return MetricService.list_guardrails_for_experiment(db, experiment_id)
