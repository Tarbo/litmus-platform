from sqlalchemy.orm import Session

from app.services.analysis_service import AnalysisService


class RealtimeService:
    @staticmethod
    def live_report(db: Session, experiment_id: str):
        return AnalysisService.report(db, experiment_id)
