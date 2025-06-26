"""Link endpoints package."""

from fastapi import APIRouter

from .internal import router as internal_router
from .public import router as public_router

router = APIRouter()
router.include_router(public_router)
router.include_router(internal_router)
