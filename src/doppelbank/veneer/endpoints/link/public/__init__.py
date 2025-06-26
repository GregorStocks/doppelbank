"""Public (documented) Plaid Link API endpoints."""

from fastapi import APIRouter

from .get_institution import router as get_institution_router
from .link_token_create import router as link_token_create_router
from .set_access_token import router as set_access_token_router

router = APIRouter()
router.include_router(get_institution_router)
router.include_router(link_token_create_router)
router.include_router(set_access_token_router)
