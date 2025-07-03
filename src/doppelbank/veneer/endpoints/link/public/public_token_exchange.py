"""Implementation of /item/public_token/exchange endpoint."""

import random
import uuid
from pathlib import Path

from fastapi import APIRouter

from doppelbank.lib.ids import ItemId
from doppelbank.veneer.common import VeneerRequest, VeneerResponse

router = APIRouter()


class PublicTokenExchangeRequest(VeneerRequest):
    public_token: str


class PublicTokenExchangeResponse(VeneerResponse):
    access_token: str
    item_id: str
    request_id: str


def get_available_personas() -> list[str]:
    """Get list of available personas from data directory."""
    personas_dir = Path("data/personas")
    if not personas_dir.exists():
        raise ValueError("No personas found")
    return [p.name for p in personas_dir.iterdir() if p.is_dir()]


def get_available_institutions_for_persona(persona_id: str) -> list[str]:
    """Get list of institutions available for a given persona."""
    persona_dir = Path("data/personas") / persona_id
    if not persona_dir.exists():
        raise ValueError("Persona not found")
    return [inst.name for inst in persona_dir.iterdir() if inst.is_dir()]


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
    item_id = ItemId(
        user_id=user_id, persona_id=persona_id, institution_id=institution_id
    )

    # Create access token using helper method
    access_token = item_id.create_access_token()
    request_id = uuid.uuid4().hex[:5]

    return PublicTokenExchangeResponse(
        access_token=access_token, item_id=item_id.to_wire(), request_id=request_id
    )
