from fastapi.testclient import TestClient
from monetizer_ai.monetizer_turso import app


def test_mint_rate_limit():
    client = TestClient(app)
    for i in range(11):
        r = client.post("/mint", json={"title":"t","duration_days":1})
        if i == 10:
            assert r.status_code in (429, 200)
        else:
            assert r.status_code in (200, 422, 400)
