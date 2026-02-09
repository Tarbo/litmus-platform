from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_write_access
from app.models.variant import Variant
from app.schemas.analysis import AssignmentRequest, AssignmentResponse
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix='/assignments', tags=['assignments'])


@router.post('/assign', response_model=AssignmentResponse)
def assign_user(
    payload: AssignmentRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    assignment = AssignmentService.assign_user(db, payload.experiment_id, payload.user_id)
    variant = db.scalar(select(Variant).where(Variant.id == assignment.variant_id))
    return AssignmentResponse(
        experiment_id=assignment.experiment_id,
        user_id=assignment.user_id,
        variant_id=assignment.variant_id,
        variant_name=variant.name if variant else 'unknown',
        released=assignment.released_at is not None,
    )
