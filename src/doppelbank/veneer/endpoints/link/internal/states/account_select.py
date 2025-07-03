import json
import uuid
from pathlib import Path
from typing import Any

from doppelbank.veneer.endpoints.link.internal.models import (
    WorkflowResponse,
)


def create_response() -> WorkflowResponse:
    data = load_example_response()

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

    data["next_pane"]["user_selection"]["selections"][0]["responses"] = accounts
    data["next_pane"]["id"] = "account_select"
    data["next_pane"]["user_selection"]["events"]["on_appear"][0]["metadata"]["link_session_id"] = (
        str(uuid.uuid4())
    )

    return WorkflowResponse(**data)


def load_example_response() -> dict[str, Any]:
    example_file = Path(__file__).parent / "account_select_response_template.json"
    with open(example_file) as f:
        data: dict[str, Any] = json.load(f)
        return data
