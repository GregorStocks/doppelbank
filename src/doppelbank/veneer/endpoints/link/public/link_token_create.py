import random
import string
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest, VeneerResponse
from doppelbank.veneer.webhooks import store_webhook_for_link_token

router = APIRouter()


class LinkTokenCreateRequest(VeneerRequest):
    client_name: str
    country_codes: list[str]
    language: str
    user: dict
    products: list[str]
    client_id: str | None = None
    secret: str | None = None
    webhook: str | None = None


class LinkTokenCreateResponse(VeneerResponse):
    link_token: str
    expiration: str
    request_id: str


@router.post("/link/token/create")
async def create_link_token(
    request: LinkTokenCreateRequest,
) -> LinkTokenCreateResponse:
    link_token = f"link-devenv-{uuid.uuid4()}"
    expiration = (datetime.now(UTC) + timedelta(hours=4)).replace(microsecond=0).isoformat() + "Z"
    request_id = "".join(random.choices(string.ascii_letters + string.digits, k=15))

    # Store webhook URL if provided
    if request.webhook:
        store_webhook_for_link_token(link_token, request.webhook)

    return LinkTokenCreateResponse(
        link_token=link_token, expiration=expiration, request_id=request_id
    )
