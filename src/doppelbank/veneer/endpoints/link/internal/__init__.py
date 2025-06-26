"""Internal (undocumented) Link workflow API endpoints reverse-engineered from network traffic."""

from fastapi import APIRouter

from .heartbeat import router as heartbeat_router
from .workflow import router as workflow_router
from .workflow_event import router as workflow_event_router
from .workflow_poll import router as workflow_poll_router

router = APIRouter()
router.include_router(heartbeat_router)
router.include_router(workflow_router)
router.include_router(workflow_poll_router)
router.include_router(workflow_event_router)
