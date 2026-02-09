import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.analysis_service import AnalysisService

router = APIRouter(prefix='/ws', tags=['websocket'])


@router.websocket('/experiments/{experiment_id}/live')
async def experiment_live(websocket: WebSocket, experiment_id: str):
    await websocket.accept()
    try:
        while True:
            db = websocket.app.state.session_maker()
            try:
                report = AnalysisService.report(db, experiment_id)
                report['status'] = report['status'].value
                report['last_updated_at'] = report['last_updated_at'].isoformat()
                await websocket.send_text(json.dumps(report))
            finally:
                db.close()
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
