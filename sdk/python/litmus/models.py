from dataclasses import dataclass
from typing import Any


@dataclass
class Experiment:
    id: str
    name: str
    status: str
    sample_size_required: int

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> 'Experiment':
        return Experiment(
            id=payload['id'],
            name=payload['name'],
            status=payload['status'],
            sample_size_required=payload.get('sample_size_required', 0),
        )


@dataclass
class ExperimentReport:
    experiment_id: str
    recommendation: str
    confidence: float
    p_value: float
    sample_progress: float

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> 'ExperimentReport':
        return ExperimentReport(
            experiment_id=payload['experiment_id'],
            recommendation=payload['recommendation'],
            confidence=payload['confidence'],
            p_value=payload['p_value'],
            sample_progress=payload['sample_progress'],
        )
