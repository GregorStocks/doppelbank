"""Implementation of /item/public_token/exchange endpoint."""

import random
import uuid

from fastapi import APIRouter

from doppelbank.lib.ids import ItemId
from doppelbank.veneer.common import VeneerRequest, VeneerResponse
from doppelbank.veneer.data import get_available_institutions_for_persona, get_available_personas

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
    # Generate a realistic hierarchical ID using available data
    user_id = f"user_{uuid.uuid4().hex[:8]}"

    # Select a random persona and institution from available data
    personas = get_available_personas()
    persona_id = random.choice(personas)

    institutions = get_available_institutions_for_persona(persona_id)
    institution_id = random.choice(institutions)

    # Create item ID using hierarchical structure
    item_id = ItemId(user_id=user_id, persona_id=persona_id, institution_id=institution_id)

    # Create access token using helper method
    access_token = item_id.create_access_token()
    request_id = uuid.uuid4().hex[:5]

    return PublicTokenExchangeResponse(
        access_token=access_token, item_id=item_id.to_wire(), request_id=request_id
    )
