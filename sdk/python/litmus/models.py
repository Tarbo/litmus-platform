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


@dataclass
class Assignment:
    experiment_id: str
    assignment_id: str
    unit_id: str
    variant_key: str
    config_json: dict[str, Any]
    experiment_version: int

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> 'Assignment':
        return Assignment(
            experiment_id=payload['experiment_id'],
            assignment_id=payload['assignment_id'],
            unit_id=payload['unit_id'],
            variant_key=payload['variant_key'],
            config_json=payload.get('config_json', {}),
            experiment_version=payload.get('experiment_version', 0),
        )


@dataclass
class BatchIngestResult:
    ingested: int

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> 'BatchIngestResult':
        return BatchIngestResult(ingested=payload.get('ingested', 0))
