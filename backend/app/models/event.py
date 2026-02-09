import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Event(Base, TimestampMixin):
    __tablename__ = 'events'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    variant_id: Mapped[str | None] = mapped_column(ForeignKey('variants.id', ondelete='SET NULL'), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    period: Mapped[str] = mapped_column(String(20), default='post', index=True)
    value: Mapped[float] = mapped_column(Float, default=1.0)

    experiment = relationship('Experiment', back_populates='events')
    variant = relationship('Variant', back_populates='events')
