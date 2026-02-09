import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Variant(Base, TimestampMixin):
    __tablename__ = 'variants'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    traffic_allocation: Mapped[float] = mapped_column(Float, nullable=False)

    experiment = relationship('Experiment', back_populates='variants')
    assignments = relationship('Assignment', back_populates='variant')
    events = relationship('Event', back_populates='variant')
