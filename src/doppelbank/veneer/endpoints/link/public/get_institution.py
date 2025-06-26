import uuid
from typing import Any

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerResponse

router = APIRouter()


class InstitutionResponse(VeneerResponse):
    institution: dict[str, Any]
    request_id: str


@router.get("/api/institution/{institution_id}")
async def get_institution(institution_id: str) -> InstitutionResponse:
    # Mock institution data
    institution = {
        "institution_id": institution_id,
        "name": "Demo Bank",
        "logo": (
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
            "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        ),
        "products": ["auth", "transactions", "identity"],
        "country_codes": ["US"],
        "url": "https://demobank.com",
        "primary_color": "#003d6b",
    }

    request_id = str(uuid.uuid4())

    return InstitutionResponse(institution=institution, request_id=request_id)
