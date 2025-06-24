from fastapi.testclient import TestClient
from doppelbank.veneer.cli import app

client = TestClient(app)

def test_transactions_sync():
    response = client.get("/transactions/sync")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "events" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) > 0 