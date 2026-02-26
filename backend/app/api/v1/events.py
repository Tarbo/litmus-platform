from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_write_access
from app.schemas.event import (
    BatchIngestResponse,
    EventCreate,
    EventResponse,
    ExposureEventCreate,
    MetricEventCreate,
)
from app.services.event_service import EventService

router = APIRouter(prefix='/events', tags=['events'])


@router.post('', response_model=EventResponse)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    event = EventService.ingest_event(db, payload)
    return EventService.serialize_event(event)


@router.post('/exposure', response_model=BatchIngestResponse)
def create_exposure(
    payload: ExposureEventCreate | list[ExposureEventCreate],
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    if isinstance(payload, list):
        return BatchIngestResponse(ingested=EventService.ingest_exposure_batch(db, payload))
    EventService.ingest_exposure(db, payload)
    return BatchIngestResponse(ingested=1)


@router.post('/metric', response_model=BatchIngestResponse)
def create_metric(
    payload: MetricEventCreate | list[MetricEventCreate],
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    if isinstance(payload, list):
        return BatchIngestResponse(ingested=EventService.ingest_metric_batch(db, payload))
    EventService.ingest_metric(db, payload)
    return BatchIngestResponse(ingested=1)
