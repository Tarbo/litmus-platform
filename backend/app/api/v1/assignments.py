import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_write_access
from app.models.variant import Variant
from app.schemas.analysis import AssignmentRequest, AssignmentResponse
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix='/assignments', tags=['assignments'])


def _build_response(db: Session, assignment, experiment_version: int) -> AssignmentResponse:
    variant = db.scalar(select(Variant).where(Variant.id == assignment.variant_id))
    config_payload: dict = {}
    variant_key = 'control'
    if variant is not None:
        variant_key = variant.key
        try:
            parsed = json.loads(variant.config_json)
            if isinstance(parsed, dict):
                config_payload = parsed
        except json.JSONDecodeError:
            config_payload = {}

    return AssignmentResponse(
        experiment_id=assignment.experiment_id,
        assignment_id=assignment.id,
        unit_id=assignment.user_id,
        variant_key=variant_key,
        config_json=config_payload,
        experiment_version=experiment_version,
    )


@router.post('', response_model=AssignmentResponse)
def assign_variant(
    payload: AssignmentRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    assignment, experiment_version = AssignmentService.assign_unit(
        db=db,
        experiment_id=payload.experiment_id,
        unit_id=payload.unit_id,
        attributes=payload.attributes or {},
    )
    return _build_response(db, assignment, experiment_version)


@router.post('/assign', response_model=AssignmentResponse)
def assign_user_legacy(
    payload: AssignmentRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    assignment, experiment_version = AssignmentService.assign_unit(
        db=db,
        experiment_id=payload.experiment_id,
        unit_id=payload.unit_id,
        attributes=payload.attributes or {},
    )
    return _build_response(db, assignment, experiment_version)
