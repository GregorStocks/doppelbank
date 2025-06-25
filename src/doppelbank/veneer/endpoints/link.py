"""Link token endpoints for Plaid API compatibility."""

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class LinkTokenCreateRequest(BaseModel):
    """Request model for /link/token/create."""

    client_name: str
    country_codes: list[str]
    language: str
    user: dict
    products: list[str]
    client_id: str | None = None
    secret: str | None = None


class LinkTokenCreateResponse(BaseModel):
    """Response model for /link/token/create."""

    link_token: str
    expiration: str
    request_id: str


class LinkWorkflowStartRequest(BaseModel):
    """Request model for /link/workflow/start."""

    link_token: str
    client_id: str | None = None
    secret: str | None = None


class LinkWorkflowStartResponse(BaseModel):
    """Response model for /link/workflow/start."""

    workflow_id: str
    request_id: str


@router.post("/link/token/create")
async def create_link_token(
    _request: LinkTokenCreateRequest,
) -> LinkTokenCreateResponse:
    """Create a link token for Plaid Link initialization.

    This generates random values but matches Plaid's exact format.
    """
    import random
    import string
    from datetime import datetime, timedelta

    # Generate link token in Plaid's format: link-devenv-{uuid}
    # "devenv" is magic which tells Link to talk to localhost:8082 :|
    link_token = f"link-devenv-{uuid.uuid4()}"

    # Generate expiration 4 hours from now, no microseconds, format: YYYY-MM-DDTHH:MM:SSZ
    expiration = (datetime.utcnow() + timedelta(hours=4)).replace(
        microsecond=0
    ).isoformat() + "Z"

    # Generate request_id in Plaid's format: short alphanumeric string like "XQVgFigpGHXkb0b"
    request_id = "".join(random.choices(string.ascii_letters + string.digits, k=15))

    return LinkTokenCreateResponse(
        link_token=link_token, expiration=expiration, request_id=request_id
    )


@router.post("/link/workflow/start")
async def start_link_workflow(
    _request: LinkWorkflowStartRequest,
) -> LinkWorkflowStartResponse:
    """Start a Link workflow session.

    This accepts a link token and returns a workflow ID for the session.
    """
    import random
    import string

    # Generate workflow_id in a format similar to Plaid's
    workflow_id = f"workflow-{uuid.uuid4()}"

    # Generate request_id in Plaid's format
    request_id = "".join(random.choices(string.ascii_letters + string.digits, k=15))

    return LinkWorkflowStartResponse(workflow_id=workflow_id, request_id=request_id)
