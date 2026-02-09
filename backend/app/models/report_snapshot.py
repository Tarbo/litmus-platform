import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ReportSnapshot(Base):
    __tablename__ = 'report_snapshots'

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id', ondelete='CASCADE'), index=True)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
