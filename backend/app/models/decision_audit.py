import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class DecisionSource(str, enum.Enum):
    auto = 'auto'
    manual = 'manual'


class DecisionAudit(Base):
    __tablename__ = 'decision_audits'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[DecisionSource] = mapped_column(Enum(DecisionSource), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), default='system')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
