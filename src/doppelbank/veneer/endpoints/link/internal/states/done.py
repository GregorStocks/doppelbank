import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from doppelbank.veneer.endpoints.accounts import get_accounts
from doppelbank.veneer.endpoints.link.internal.models import (
    WorkflowNextRequest,
    WorkflowResponse,
)
from doppelbank.veneer.webhooks import get_workflow_session


def create_response(request: WorkflowNextRequest) -> WorkflowResponse:
    data = load_example_response()

    # Use hard-coded token for testing
    public_token = "beep boop token token"
    data["next_pane"]["sink"]["public_token"] = public_token
    data["next_pane"]["sink"]["result"]["public_token"] = public_token
    data["next_pane"]["id"] = "done"
    data["workflow_session_id"] = request.workflow_session_id

    workflow = get_workflow_session(request.workflow_session_id)
    if not workflow:
        raise HTTPException(
            status_code=404, detail=f"Workflow session {request.workflow_session_id} not found"
        )

    if not workflow.item_id:
        raise HTTPException(
            status_code=404, detail=f"Workflow session {request.workflow_session_id} has no item ID"
        )

    accounts = get_accounts(workflow.item_id)

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
