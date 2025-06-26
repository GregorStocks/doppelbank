"""Internal (undocumented) Link workflow API endpoints reverse-engineered from network traffic."""

from fastapi import APIRouter

from .heartbeat import router as heartbeat_router
from .workflow_event import router as workflow_event_router
from .workflow_next import router as workflow_next_router
from .workflow_poll import router as workflow_poll_router
from .workflow_start import router as workflow_start_router

router = APIRouter()
router.include_router(heartbeat_router)
router.include_router(workflow_event_router)
router.include_router(workflow_next_router)
router.include_router(workflow_poll_router)
router.include_router(workflow_start_router)
