"""Implementation of /item/public_token/exchange endpoint."""

import uuid

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest, VeneerResponse

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
    access_token = f"test_account"
    item_id = f"item-{uuid.uuid4().hex[:32]}"
    request_id = uuid.uuid4().hex[:5]

    return PublicTokenExchangeResponse(
        access_token=access_token, item_id=item_id, request_id=request_id
    )
