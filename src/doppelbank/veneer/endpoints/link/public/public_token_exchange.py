"""Implementation of /item/public_token/exchange endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from doppelbank.veneer.common import VeneerRequest, VeneerResponse
from doppelbank.veneer.webhooks import get_workflow_session_from_link_token

router = APIRouter()


class PublicTokenExchangeRequest(VeneerRequest):
    public_token: str


class PublicTokenExchangeResponse(VeneerResponse):
    access_token: str
    item_id: str
    request_id: str


@router.post("/item/public_token/exchange", response_model=PublicTokenExchangeResponse)
async def public_token_exchange(
    _request: PublicTokenExchangeRequest,
) -> PublicTokenExchangeResponse:
    workflow_session = get_workflow_session_from_link_token(_request.public_token)
    item_id = workflow_session.item_id
    if not item_id:
        raise HTTPException(status_code=400, detail="No item ID found for link token")

    # Create access token using helper method
    access_token = item_id.create_access_token()
    request_id = uuid.uuid4().hex[:5]

    return PublicTokenExchangeResponse(
        access_token=access_token, item_id=item_id.to_wire(), request_id=request_id
    )
