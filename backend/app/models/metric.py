import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class GuardrailDirection(str, enum.Enum):
    max = 'max'
    min = 'min'


class GuardrailStatus(str, enum.Enum):
    healthy = 'healthy'
    breached = 'breached'


class Metric(Base):
    __tablename__ = 'metrics'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[GuardrailDirection] = mapped_column(Enum(GuardrailDirection), nullable=False)
    status: Mapped[GuardrailStatus] = mapped_column(Enum(GuardrailStatus), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
