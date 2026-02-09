from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreate


class EventService:
    @staticmethod
    def ingest_event(db: Session, payload: EventCreate) -> Event:
        event = Event(
            experiment_id=payload.experiment_id,
            user_id=payload.user_id,
            variant_id=payload.variant_id,
            event_type=payload.event_type,
            period=payload.period,
            value=payload.value,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
