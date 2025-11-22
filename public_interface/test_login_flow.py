from fastapi.testclient import TestClient
import public_interface.public_interface as pi


def test_login_then_fetch_embed(monkeypatch):
    """Simulate mint+login+embed flow by mocking Monetizer verify and Curator video metadata."""
    # Mock Monetizer /verify
    def fake_get(url, params=None, timeout=None, **kwargs):
        class Dummy:
            def __init__(self, status, data):
                self.status_code = status
                self._data = data
                self.text = str(data)

            def raise_for_status(self):
                if not (200 <= self.status_code < 300):
                    raise Exception('HTTP Error')

            def json(self):
                return self._data

        if '/verify' in url:
            return Dummy(200, {"ok": True, "access_level": "vip", "video_id": None, "code": "OM43-TEST"})

        if '/videos/' in url:
            return Dummy(200, {
                "id": 123,
                "bunny_video_id": "vid123",
                "library_type": "private",
                "access_level": "vip",
                "title": "Test Video",
                "cdn_hostname": "example.com"
            })

        raise RuntimeError('Unexpected URL: ' + url)

    monkeypatch.setattr('requests.get', fake_get)

    # Mock secure embed generator
    def fake_signed(library_id, video_id, security_key=None, autoplay=True, expires_in_hours=2):
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?token=MOCK&expires=999999"

    monkeypatch.setattr(pi, 'get_secure_embed_url', fake_signed)

    client = TestClient(pi.app)

    # Login with short code
    r = client.post('/api/login', json={'token': 'OM43-TEST'})
    assert r.status_code == 200
    # Cookie should be set
    assert 'access_token' in r.cookies

    # Now fetch embed for a video the token should allow
    r2 = client.get('/api/embed/123')
    assert r2.status_code == 200
    body = r2.json()
    assert body.get('ok') is True
    assert 'embed_url' in body
    assert 'token=' in body['embed_url']

    # Also ensure long token format is accepted in login
    r3 = client.post('/api/login', json={'token': 'LONG-BASE64-TOKEN-VALUE-EXAMPLE'})
    assert r3.status_code == 200
    assert 'access_token' in r3.cookies
