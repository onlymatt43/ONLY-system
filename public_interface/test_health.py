from fastapi.testclient import TestClient
from public_interface.public_interface import app


def test_head_root():
    client = TestClient(app)
    r = client.head("/")
    assert r.status_code == 200


def test_head_health():
    client = TestClient(app)
    r = client.head("/health")
    assert r.status_code == 200
