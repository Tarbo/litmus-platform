from sqlalchemy.orm import Session

from app.services.experiment_service import ExperimentService


class AnalysisService:
    @staticmethod
    def report(db: Session, experiment_id: str):
        experiment = ExperimentService.get_experiment(db, experiment_id)
        return ExperimentService.build_report(db, experiment)
