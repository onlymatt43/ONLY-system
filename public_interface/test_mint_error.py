import json
from fastapi.testclient import TestClient
from public_interface.public_interface import app


def test_mint_non_json_response(monkeypatch):
    # Simulate Monetizer responding with empty or non-json content
    class DummyResp:
        status_code = 200
        text = ""
        def raise_for_status(self):
            return None
        def json(self):
            raise ValueError("No JSON")

    def fake_post(*args, **kwargs):
        return DummyResp()

    monkeypatch.setattr("requests.post", fake_post)

    client = TestClient(app)
    r = client.post("/api/tokens/mint", json={"title":"test"})
    assert r.status_code == 502
    data = r.json()
    assert "invalid" in data["detail"] or "Monetizer" in data["detail"]
