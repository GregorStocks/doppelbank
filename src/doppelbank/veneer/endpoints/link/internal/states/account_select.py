import json
import uuid
from pathlib import Path
from typing import Any

from doppelbank.lib.ids import ItemId
from doppelbank.veneer.endpoints.accounts import get_accounts
from doppelbank.veneer.endpoints.link.internal.models import (
    WorkflowResponse,
)


def create_response() -> tuple[WorkflowResponse, ItemId]:
    data = load_example_response()

    user_id = "fakeuser"
    persona = "jimmy"
    institution = "doppelbank"

    item_id = ItemId(user_id, persona, institution)
    accounts = get_accounts(item_id)

    data["next_pane"]["user_selection"]["selections"][0]["responses"] = [
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
    data["next_pane"]["id"] = "account_select"
    data["next_pane"]["user_selection"]["events"]["on_appear"][0]["metadata"]["link_session_id"] = (
        str(uuid.uuid4())
    )
    data["workflow_session_id"] = str(uuid.uuid4())

    return WorkflowResponse(**data), item_id


def load_example_response() -> dict[str, Any]:
    example_file = Path(__file__).parent / "account_select_response_template.json"
    with open(example_file) as f:
        data: dict[str, Any] = json.load(f)
        return data
