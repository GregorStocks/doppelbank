import json
import logging
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from doppelbank.veneer.endpoints.accounts import get_accounts
from doppelbank.veneer.endpoints.link.internal.models import (
    WorkflowNextRequest,
    WorkflowResponse,
)
from doppelbank.veneer.webhooks import get_workflow_session

logger = logging.getLogger(__name__)


def create_response(request: WorkflowNextRequest) -> WorkflowResponse:
    workflow_session = get_workflow_session(request.workflow_session_id)
    if not workflow_session:
        raise HTTPException(
            status_code=404, detail=f"Workflow session {request.workflow_session_id} not found"
        )
    if not workflow_session.item_id:
        raise HTTPException(
            status_code=404, detail=f"Workflow session {request.workflow_session_id} has no item ID"
        )

    data = load_example_response()

    data["next_pane"]["id"] = "done"
    data["workflow_session_id"] = workflow_session.session_id

    public_token = workflow_session.public_token
    data["next_pane"]["sink"]["public_token"] = public_token
    data["next_pane"]["sink"]["result"]["public_token"] = public_token

    logger.info(f"Done {workflow_session.session_id=} {public_token=}")

    accounts = get_accounts(workflow_session.item_id)

    data["next_pane"]["sink"]["result"]["metadata"]["accounts"] = [
        {
            "id": account.account_id,
            "title": {"translation": account.name},
            "note": None,
            "subtitle": None,
            "detail": {"translation": f"${account.balances.current}"},
            "preselected": True,
            "trailing_icon": "SDK_ASSET_UNKNOWN",
            "on_submit": None,
            "children": [],
            "leading_asset": None,
            "trailing_asset": None,
        }
        for account in accounts
    ]

    return WorkflowResponse(**data)


def load_example_response() -> dict[str, Any]:
    example_file = Path(__file__).parent / "done_response_template.json"
    with open(example_file) as f:
        data: dict[str, Any] = json.load(f)
        return data
