import uuid
from typing import Any

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest, VeneerResponse

router = APIRouter()


class SetAccessTokenRequest(VeneerRequest):
    public_token: str
    metadata: dict[str, Any]


class SetAccessTokenResponse(VeneerResponse):
    access_token: str
    item_id: str
    accounts: list[dict[str, Any]]
    request_id: str


@router.post("/api/set_access_token")
async def set_access_token(
    request: SetAccessTokenRequest,
) -> SetAccessTokenResponse:
    # Mock access token and item ID
    access_token = f"access-mock-{uuid.uuid4()}"
    item_id = f"item-mock-{uuid.uuid4()}"

    # Echo back accounts from metadata
    accounts = request.metadata.get(
        "accounts",
        [
            {
                "account_id": f"acc-{uuid.uuid4()}",
                "name": "Demo Checking",
                "type": "depository",
                "subtype": "checking",
            }
        ],
    )

    request_id = str(uuid.uuid4())

    return SetAccessTokenResponse(
        access_token=access_token,
        item_id=item_id,
        accounts=accounts,
        request_id=request_id,
    )
