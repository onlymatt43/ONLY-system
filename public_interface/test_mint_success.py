from fastapi.testclient import TestClient
import public_interface.public_interface as pi


def test_mint_success(monkeypatch):
    class DummyResp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"ok": True, "code": "OM43-TEST", "token": "LONGTOKEN"}

    def fake_post(*args, **kwargs):
        return DummyResp()

    monkeypatch.setattr('requests.post', fake_post)

    client = TestClient(pi.app)
    r = client.post('/api/tokens/mint', json={"title": "t"})
    assert r.status_code == 200
    data = r.json()
    assert data.get('ok') is True
    assert 'code' in data
