"""Public (documented) Plaid Link API endpoints."""

from fastapi import APIRouter

from .get_institution import router as get_institution_router
from .link_token_create import router as link_token_create_router
from .public_token_exchange import router as public_token_exchange_router

router = APIRouter()
router.include_router(get_institution_router)
router.include_router(link_token_create_router)
router.include_router(public_token_exchange_router)
