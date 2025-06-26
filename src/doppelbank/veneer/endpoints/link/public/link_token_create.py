import random
import string
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest, VeneerResponse

router = APIRouter()


class LinkTokenCreateRequest(VeneerRequest):
    client_name: str
    country_codes: list[str]
    language: str
    user: dict
    products: list[str]
    client_id: str | None = None
    secret: str | None = None


class LinkTokenCreateResponse(VeneerResponse):
    link_token: str
    expiration: str
    request_id: str


@router.post("/link/token/create")
async def create_link_token(
    _request: LinkTokenCreateRequest,
) -> LinkTokenCreateResponse:

    link_token = f"link-devenv-{uuid.uuid4()}"
    expiration = (datetime.utcnow() + timedelta(hours=4)).replace(
        microsecond=0
    ).isoformat() + "Z"
    request_id = "".join(random.choices(string.ascii_letters + string.digits, k=15))

    return LinkTokenCreateResponse(
        link_token=link_token, expiration=expiration, request_id=request_id
    )
