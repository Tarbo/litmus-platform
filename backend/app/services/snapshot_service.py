import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report_snapshot import ReportSnapshot


class SnapshotService:
    @staticmethod
    def create_snapshot(db: Session, experiment_id: str, report_payload: dict) -> ReportSnapshot:
        snapshot = ReportSnapshot(experiment_id=experiment_id, snapshot_json=json.dumps(report_payload))
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def list_snapshots(db: Session, experiment_id: str, limit: int = 20) -> list[ReportSnapshot]:
        return db.scalars(
            select(ReportSnapshot)
            .where(ReportSnapshot.experiment_id == experiment_id)
            .order_by(ReportSnapshot.created_at.desc())
            .limit(limit)
        ).all()
