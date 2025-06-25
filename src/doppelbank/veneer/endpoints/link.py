"""Link token endpoints for Plaid API compatibility."""

import uuid
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class LinkTokenCreateRequest(BaseModel):
    """Request model for /link/token/create."""
    client_name: str
    country_codes: List[str]
    language: str
    user: dict
    products: List[str]
    client_id: Optional[str] = None
    secret: Optional[str] = None


class LinkTokenCreateResponse(BaseModel):
    """Response model for /link/token/create."""
    link_token: str
    expiration: str
    request_id: str


@router.post("/link/token/create")
async def create_link_token(request: LinkTokenCreateRequest) -> LinkTokenCreateResponse:
    """Create a link token for Plaid Link initialization.
    
    This generates random values but matches Plaid's exact format.
    """
    import random
    import string
    from datetime import datetime, timedelta
    
    # Generate link token in Plaid's format: link-sandbox-{uuid}
    link_token = f"link-sandbox-{uuid.uuid4()}"
    
    # Generate expiration 4 hours from now, no microseconds, format: YYYY-MM-DDTHH:MM:SSZ
    expiration = (datetime.utcnow() + timedelta(hours=4)).replace(microsecond=0).isoformat() + "Z"
    
    # Generate request_id in Plaid's format: short alphanumeric string like "XQVgFigpGHXkb0b"
    request_id = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    
    return LinkTokenCreateResponse(
        link_token=link_token,
        expiration=expiration,
        request_id=request_id
    )