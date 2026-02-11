import enum
import json
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class ExperimentStatus(str, enum.Enum):
    DRAFT = 'DRAFT'
    RUNNING = 'RUNNING'
    PAUSED = 'PAUSED'
    STOPPED = 'STOPPED'
    # Backward-compatible aliases used by existing modules during migration.
    draft = DRAFT
    running = RUNNING
    paused = PAUSED
    stopped = STOPPED
    passed = STOPPED
    failed = STOPPED
    inconclusive = STOPPED
    terminated_without_cause = STOPPED


class Experiment(Base, TimestampMixin):
    __tablename__ = 'experiments'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default='', nullable=False)
    owner_team: Mapped[str] = mapped_column(String(120), default='unknown-team', nullable=False)
    created_by: Mapped[str] = mapped_column(String(120), default='system', nullable=False)
    unit_type: Mapped[str] = mapped_column(String(80), default='user_id', nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, default='[]', nullable=False)
    targeting_json: Mapped[str] = mapped_column(Text, default='{}', nullable=False)
    ramp_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    assignment_salt: Mapped[str] = mapped_column(String(64), default=lambda: uuid.uuid4().hex, nullable=False)

    # Legacy statistical fields kept for backward compatibility with existing report surface.
    hypothesis: Mapped[str] = mapped_column(Text, default='', nullable=False)
    mde: Mapped[float] = mapped_column(Float, default=0.05)
    baseline_rate: Mapped[float] = mapped_column(Float, default=0.1)
    alpha: Mapped[float] = mapped_column(Float, default=0.05)
    power: Mapped[float] = mapped_column(Float, default=0.8)
    sample_size_required: Mapped[int] = mapped_column(default=1000)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    variants = relationship('Variant', back_populates='experiment', cascade='all, delete-orphan')
    assignments = relationship('Assignment', back_populates='experiment', cascade='all, delete-orphan')
    events = relationship('Event', back_populates='experiment', cascade='all, delete-orphan')

    @property
    def tags(self) -> list[str]:
        try:
            payload = json.loads(self.tags_json)
            return payload if isinstance(payload, list) else []
        except json.JSONDecodeError:
            return []

    @property
    def targeting(self) -> dict:
        try:
            payload = json.loads(self.targeting_json)
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}
