import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.variant import Variant
from app.schemas.event import EventCreate, ExposureEventCreate, MetricEventCreate


class EventService:
    @staticmethod
    def _resolve_variant(db: Session, experiment_id: str, variant_key: str) -> Variant:
        variant = db.scalar(
            select(Variant).where(
                Variant.experiment_id == experiment_id,
                Variant.key == variant_key,
            )
        )
        if variant is None:
            raise HTTPException(status_code=404, detail=f'Variant key not found: {variant_key}')
        return variant

    @staticmethod
    def _to_payload_context(context: dict | None) -> str:
        return json.dumps(context or {})

    @staticmethod
    def _normalize_ts(ts: datetime | None) -> datetime:
        return ts or datetime.now(timezone.utc)

    @staticmethod
    def ingest_event(db: Session, payload: EventCreate) -> Event:
        event = Event(
            experiment_id=payload.experiment_id,
            user_id=payload.user_id,
            variant_id=payload.variant_id,
            event_type=payload.event_type,
            metric_name=payload.metric_name,
            period=payload.period,
            value=payload.value,
            context_json=EventService._to_payload_context(payload.context_json),
            observed_at=EventService._normalize_ts(payload.observed_at),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def ingest_exposure(db: Session, payload: ExposureEventCreate) -> Event:
        variant = EventService._resolve_variant(db, payload.experiment_id, payload.variant_key)
        event = Event(
            experiment_id=payload.experiment_id,
            user_id=payload.unit_id,
            variant_id=variant.id,
            event_type='exposure',
            period='post',
            value=1.0,
            context_json=EventService._to_payload_context(payload.context),
            observed_at=EventService._normalize_ts(payload.ts),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def ingest_exposure_batch(db: Session, payloads: list[ExposureEventCreate]) -> int:
        for payload in payloads:
            variant = EventService._resolve_variant(db, payload.experiment_id, payload.variant_key)
            db.add(
                Event(
                    experiment_id=payload.experiment_id,
                    user_id=payload.unit_id,
                    variant_id=variant.id,
                    event_type='exposure',
                    period='post',
                    value=1.0,
                    context_json=EventService._to_payload_context(payload.context),
                    observed_at=EventService._normalize_ts(payload.ts),
                )
            )
        db.commit()
        return len(payloads)

    @staticmethod
    def ingest_metric(db: Session, payload: MetricEventCreate) -> Event:
        variant = EventService._resolve_variant(db, payload.experiment_id, payload.variant_key)
        event = Event(
            experiment_id=payload.experiment_id,
            user_id=payload.unit_id,
            variant_id=variant.id,
            event_type='metric',
            metric_name=payload.metric_name,
            period='post',
            value=payload.value,
            context_json=EventService._to_payload_context(payload.context),
            observed_at=EventService._normalize_ts(payload.ts),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def ingest_metric_batch(db: Session, payloads: list[MetricEventCreate]) -> int:
        for payload in payloads:
            variant = EventService._resolve_variant(db, payload.experiment_id, payload.variant_key)
            db.add(
                Event(
                    experiment_id=payload.experiment_id,
                    user_id=payload.unit_id,
                    variant_id=variant.id,
                    event_type='metric',
                    metric_name=payload.metric_name,
                    period='post',
                    value=payload.value,
                    context_json=EventService._to_payload_context(payload.context),
                    observed_at=EventService._normalize_ts(payload.ts),
                )
            )
        db.commit()
        return len(payloads)
