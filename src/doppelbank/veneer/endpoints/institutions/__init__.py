"""Institutions API endpoints."""

from fastapi import APIRouter

from .get_by_id import router as get_by_id_router

router = APIRouter()
router.include_router(get_by_id_router)
