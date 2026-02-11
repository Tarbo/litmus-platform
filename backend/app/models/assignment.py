import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Assignment(Base, TimestampMixin):
    __tablename__ = 'assignments'
    __table_args__ = (UniqueConstraint('experiment_id', 'user_id', name='uq_experiment_user_assignment'),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    variant_id: Mapped[str] = mapped_column(ForeignKey('variants.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    experiment = relationship('Experiment', back_populates='assignments')
    variant = relationship('Variant', back_populates='assignments')
