from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReportSnapshotResponse(BaseModel):
    id: str
    experiment_id: str
    snapshot: dict[str, Any]
    created_at: datetime
