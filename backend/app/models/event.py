import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Event(Base, TimestampMixin):
    __tablename__ = 'events'
    __table_args__ = (
        Index('ix_events_experiment_period_type', 'experiment_id', 'period', 'event_type'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    variant_id: Mapped[str | None] = mapped_column(ForeignKey('variants.id', ondelete='SET NULL'), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    metric_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    period: Mapped[str] = mapped_column(String(20), default='post', index=True)
    value: Mapped[float] = mapped_column(Float, default=1.0)
    context_json: Mapped[str] = mapped_column(Text, default='{}', nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    experiment = relationship('Experiment', back_populates='events')
    variant = relationship('Variant', back_populates='events')
