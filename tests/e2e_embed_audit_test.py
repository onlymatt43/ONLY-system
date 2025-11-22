import os
from fastapi.testclient import TestClient

from public_interface import public_interface as pi
from sentinel_dashboard import sentinel as sentinel_mod


def test_embed_audit_and_sentinel_read(tmp_path, monkeypatch):
    # Create log dir and ensure clean file
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    audit_path = os.path.join(logs_dir, 'public_interface_audit.log')
    if os.path.exists(audit_path):
        os.remove(audit_path)

    # Mock requests.get responses: /verify and /videos/<id>
    def fake_get(url, params=None, timeout=None, **kwargs):
        class D:
            def __init__(self, status, payload):
                self.status_code = status
                self._payload = payload
                self.text = str(payload)

            def raise_for_status(self):
                if not (200 <= self.status_code < 300):
                    raise Exception('HTTP error')

            def json(self):
                return self._payload

        if '/verify' in url:
            return D(200, {'ok': True, 'access_level': 'vip', 'code': 'OM43-FAKE'})
        if '/videos/123' in url:
            return D(200, {'id': 123, 'bunny_video_id': 'vid123', 'library_type': 'private', 'access_level': 'vip'})
        raise RuntimeError('Unexpected URL: ' + url)

    monkeypatch.setattr('requests.get', fake_get)

    # also mock Monetizer mint so login cookie will be set
    def fake_post(url, json=None, timeout=None, **kwargs):
        class R:
            status_code = 200
            def raise_for_status(self):
                return None
            def json(self):
                return {'ok': True, 'code': 'OM43-TEST', 'token': 'LONGTOKEN'}
        return R()

    monkeypatch.setattr('requests.post', fake_post)

    client = TestClient(pi.app)

    # mint (not strictly necessary but mimics flow)
    r = client.post('/api/tokens/mint', json={'title': 'T'})
    assert r.status_code == 200

    # login with code
    r2 = client.post('/api/login', json={'token': 'OM43-TEST'})
    assert r2.status_code == 200
    assert 'access_token' in r2.cookies

    # request embed which should produce an audit log entry
    r3 = client.get('/api/embed/123')
    assert r3.status_code == 200
    body = r3.json()
    assert body.get('ok') is True

    # Wait briefly for file flush and read the log
    assert os.path.exists(audit_path)
    with open(audit_path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    assert 'embed_request' in content

    # Now test sentinel reading the audit via admin key
    os.environ['SENTINEL_ADMIN_KEY'] = 'admin-test'
    fake_req = type('R', (), {'headers': {'X-Admin-Key': 'admin-test'}})()
    resp = sentinel_mod._read_audit_log(fake_req, 'public_interface_audit.log')
    assert resp.status_code == 200
    data = resp.json()
    assert data['ok']
    assert any('embed_request' in l for l in ''.join(data['lines']))
