import json
from pathlib import Path
from typing import Any

from doppelbank.veneer.endpoints.link.internal.models import (
    WorkflowNextRequest,
    WorkflowResponse,
)


def create_response(request: WorkflowNextRequest) -> WorkflowResponse:
    data = load_example_response()

    # Use hard-coded token for testing
    public_token = "beep boop token token"
    data["next_pane"]["sink"]["public_token"] = public_token
    data["next_pane"]["sink"]["result"]["public_token"] = public_token
    data["next_pane"]["id"] = "done"
    data["workflow_session_id"] = request.workflow_session_id

    accounts = [
        {
            "id": "test_account",
            "title": {"translation": "Beep • 1111"},
            "note": None,
            "subtitle": None,
            "detail": {"translation": "$200.00"},
            "preselected": True,
            "trailing_icon": "SDK_ASSET_UNKNOWN",
            "on_submit": None,
            "children": [],
            "leading_asset": None,
            "trailing_asset": None,
        }
    ]

    data["next_pane"]["sink"]["result"]["metadata"]["accounts"] = accounts

    return WorkflowResponse(**data)


def load_example_response() -> dict[str, Any]:
    example_file = Path(__file__).parent / "done_response_template.json"
    with open(example_file) as f:
        data: dict[str, Any] = json.load(f)
        return data
