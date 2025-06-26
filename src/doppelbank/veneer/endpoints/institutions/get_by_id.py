"""Implementation of /institutions/get_by_id endpoint."""

import base64
import io
import os
import uuid
from pathlib import Path

from fastapi import APIRouter
from PIL import Image

from doppelbank.veneer.common import VeneerRequest, VeneerResponse

router: APIRouter = APIRouter()


def load_doppelbank_logo() -> str:
    """Load the DoppelBank logo, resize to 152x152 PNG, and encode as base64.

    Returns raw base64 string without data URI prefix, as per Plaid API spec.
    """
    # Get resources directory from environment variable, default to ./resources
    resources_dir = os.getenv("DOPPELBANK_RESOURCES_DIR", "resources")
    logo_path = Path(resources_dir) / "doppelbank_logo.png"

    # Open and resize image to 152x152 as per Plaid spec
    with Image.open(logo_path) as img:
        img_resized = img.resize((152, 152), Image.Resampling.LANCZOS)

        # Save to memory as PNG
        img_buffer = io.BytesIO()
        img_resized.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Return raw base64 string (no data URI prefix)
        return base64.b64encode(img_buffer.getvalue()).decode("utf-8")


class InstitutionsGetByIdRequest(VeneerRequest):
    """Request model for /institutions/get_by_id endpoint."""

    institution_id: str
    country_codes: list[str]


class Institution(VeneerResponse):
    """Institution object returned by Plaid API."""

    institution_id: str
    name: str
    products: list[str]
    country_codes: list[str]
    url: str
    primary_color: str
    logo: str
    oauth: bool


class InstitutionsGetByIdResponse(VeneerResponse):
    """Response model for /institutions/get_by_id endpoint."""

    institution: Institution
    request_id: str


@router.post("/institutions/get_by_id")
def institutions_get_by_id(
    request: InstitutionsGetByIdRequest,
) -> InstitutionsGetByIdResponse:
    """Get institution details by ID.

    This mock implementation returns doppelbank institution data
    based on the requested institution_id.
    """
    institution = Institution(
        institution_id=request.institution_id,
        name="DoppelBank",
        products=["auth", "transactions", "identity", "assets"],
        country_codes=request.country_codes,
        url="https://doppelbank.com",
        primary_color="#003d6b",
        logo=load_doppelbank_logo(),
        oauth=True,
    )

    request_id = uuid.uuid4().hex[:5]

    return InstitutionsGetByIdResponse(institution=institution, request_id=request_id)
