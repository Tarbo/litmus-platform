import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Variant(Base, TimestampMixin):
    __tablename__ = 'variants'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    key: Mapped[str] = mapped_column(String(80), default=lambda: uuid.uuid4().hex[:8], nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    config_json: Mapped[str] = mapped_column(Text, default='{}', nullable=False)

    experiment = relationship('Experiment', back_populates='variants')
    assignments = relationship('Assignment', back_populates='variant')
    events = relationship('Event', back_populates='variant')

    @property
    def traffic_allocation(self) -> float:
        return self.weight

    @traffic_allocation.setter
    def traffic_allocation(self, value: float) -> None:
        self.weight = value
