from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_write_access
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix='/events', tags=['events'])


@router.post('', response_model=EventResponse)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    return EventService.ingest_event(db, payload)
