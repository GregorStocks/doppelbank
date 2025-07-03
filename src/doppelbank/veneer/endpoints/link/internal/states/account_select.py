import json
import uuid
from pathlib import Path
from typing import Any

from doppelbank.lib.ids import ItemId
from doppelbank.veneer.data import get_available_institutions_for_persona, get_available_personas
from doppelbank.veneer.endpoints.accounts import get_accounts
from doppelbank.veneer.endpoints.link.internal.models import (
    WorkflowResponse,
)
from doppelbank.veneer.webhooks import WorkflowSession


def create_response(workflow_session: WorkflowSession) -> WorkflowResponse:
    data = load_example_response()

    user_id = uuid.uuid4().hex[:8]
    persona = get_available_personas()[0]
    institution = get_available_institutions_for_persona(persona)[0]

    item_id = ItemId(user_id, persona, institution)
    accounts = get_accounts(item_id)
    workflow_session.item_id = item_id

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
    data["workflow_session_id"] = workflow_session.session_id

    return WorkflowResponse(**data)


def load_example_response() -> dict[str, Any]:
    example_file = Path(__file__).parent / "account_select_response_template.json"
    with open(example_file) as f:
        data: dict[str, Any] = json.load(f)
        return data
