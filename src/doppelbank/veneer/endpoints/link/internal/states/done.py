import json
from pathlib import Path
from typing import Any

from doppelbank.veneer.endpoints.link.internal.models import WorkflowResponse


def create_response() -> WorkflowResponse:
    data = load_example_response()

    token = "beep boop token token"
    data["next_pane"]["sink"]["public_token"] = token
    data["next_pane"]["sink"]["result"]["public_token"] = token

    return WorkflowResponse(**data)


def load_example_response() -> dict[str, Any]:
    example_file = Path(__file__).parent / "done_response_template.json"
    with open(example_file) as f:
        data: dict[str, Any] = json.load(f)
        return data
