from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix='/events', tags=['events'])


@router.post('', response_model=EventResponse)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    return EventService.ingest_event(db, payload)
