from fastapi import APIRouter

from app.api.v1.assignments import router as assignments_router
from app.api.v1.events import router as events_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.results import router as results_router
from app.api.v1.websocket import router as websocket_router

api_router = APIRouter()
api_router.include_router(experiments_router)
api_router.include_router(assignments_router)
api_router.include_router(events_router)
api_router.include_router(results_router)
api_router.include_router(websocket_router)
