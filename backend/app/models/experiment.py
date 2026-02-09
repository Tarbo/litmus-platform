import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class ExperimentStatus(str, enum.Enum):
    draft = 'draft'
    running = 'running'
    passed = 'passed'
    failed = 'failed'
    inconclusive = 'inconclusive'
    terminated_without_cause = 'terminated_without_cause'


class Experiment(Base, TimestampMixin):
    __tablename__ = 'experiments'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    mde: Mapped[float] = mapped_column(Float, default=0.05)
    baseline_rate: Mapped[float] = mapped_column(Float, default=0.1)
    alpha: Mapped[float] = mapped_column(Float, default=0.05)
    power: Mapped[float] = mapped_column(Float, default=0.8)
    sample_size_required: Mapped[int] = mapped_column(default=1000)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.draft, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    variants = relationship('Variant', back_populates='experiment', cascade='all, delete-orphan')
    assignments = relationship('Assignment', back_populates='experiment', cascade='all, delete-orphan')
    events = relationship('Event', back_populates='experiment', cascade='all, delete-orphan')
