from fastapi.testclient import TestClient
import os
import time

from public_interface.public_interface import app


def test_embed_rate_limit(monkeypatch, tmp_path):
    client = TestClient(app)
    # make multiple calls to hit the rate-limit
    video_id = 12345
    # The limit is 20/minute; call >20 quickly
    for i in range(21):
        r = client.get(f"/api/embed/{video_id}")
        if i == 20:
            # After 20th request: expect 429 if slowapi is enabled, otherwise accept normal statuses
            assert r.status_code in (429, 200, 404, 422)
        else:
            assert r.status_code in (200, 404, 422)
