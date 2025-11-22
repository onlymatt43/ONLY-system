from fastapi.testclient import TestClient
import json
import os

from sentinel_dashboard.sentinel import app
from sentinel_dashboard import sentinel as sentinel_mod


def test_verify_bunny_no_key():
    try:
        client = TestClient(app)
        r = client.post('/api/verify/bunny/videoX')
        assert r.status_code == 401
    except TypeError:
        fake_req = type('R', (), {'headers': {}})()
        try:
            sentinel_mod.verify_bunny(fake_req, 'videoX')
            assert False, 'Expected HTTPException for missing admin key'
        except Exception as e:
            # direct call yields HTTPException
            assert hasattr(e, 'status_code')


def test_verify_bunny_with_key_and_probe(monkeypatch):
    # Arrange
    os.environ['SENTINEL_ADMIN_KEY'] = 'secret123'
    os.environ['BUNNY_PRIVATE_LIBRARY_ID'] = '111'
    os.environ['BUNNY_SECURITY_KEY'] = 'test-secret'

    # Mock signer
    def fake_signed(library_id, video_id, security_key=None, expires_in_hours=2, autoplay=True):
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?token=MOCKTOKEN&expires=12345"

    monkeypatch.setattr('public_interface.bunny_signer.get_secure_embed_url', fake_signed)

    # Mock probe
    class Dummy:
        status_code = 200
        reason = 'OK'

    def fake_head(url, timeout=None, allow_redirects=True):
        return Dummy()

    monkeypatch.setattr('requests.head', fake_head)

    # Act
    try:
        client = TestClient(app)
        r = client.post('/api/verify/bunny/videoX?probe=true', headers={'X-Admin-Key': 'secret123'})
        assert r.status_code == 200
        data = r.json()
        assert data['ok'] is True
        assert data['token_present'] is True
        assert data['probe_ok'] is True
        assert 'token_masked' in data and data['token_masked'].startswith('MOCK') == False
    except TypeError:
        # Fallback to direct call
        fake_req = type('R', (), {'headers': {'X-Admin-Key': 'secret123'}})()
        resp = sentinel_mod.verify_bunny(fake_req, 'videoX', library='private', probe=True)
        assert resp.status_code == 200
        # When calling the handler directly we get a JSONResponse instance which
        # doesn't have a `.json()` helper, so parse the bytes body instead.
        if hasattr(resp, 'json'):
            data = resp.json()
        else:
            data = json.loads(resp.body)
        assert data['ok'] is True
        assert data['token_present'] is True
        assert data['probe_ok'] is True
