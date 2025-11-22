from fastapi.testclient import TestClient
import os

from sentinel_dashboard.sentinel import app
from sentinel_dashboard import sentinel as sentinel_mod
from fastapi import HTTPException


def test_audit_endpoint_no_key():
    # Some test environments have an incompatible TestClient/httpx pair and
    # instantiating TestClient may raise a TypeError. In that case we fall back
    # to calling the endpoint function directly.
    try:
        client = TestClient(app)
        r = client.get('/api/audit/public_interface_audit.log')
        # Accept 401 (admin key missing) or 404 (log not yet created)
        assert r.status_code in (401, 404)
    except TypeError:
        # Call the function directly - it should raise HTTPException for missing key
        fake_req = type('R', (), {'headers': {}})()
        try:
            sentinel_mod.get_audit_log(fake_req, 'public_interface_audit.log')
            assert False, 'Expected HTTPException for missing admin key'
        except HTTPException as e:
            assert e.status_code in (401, 404)


def test_audit_endpoint_with_key():
    # Create a fake log file
    logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    p = os.path.join(logs_dir, 'test_audit.log')
    with open(p, 'w') as f:
        f.write('line1\nline2\n')

    import os
    os.environ['SENTINEL_ADMIN_KEY'] = 'secret123'
    try:
        client = TestClient(app)
        r = client.get('/api/audit/test_audit.log', headers={'X-Admin-Key': 'secret123'})
        assert r.status_code == 200
        data = r.json()
        assert data['ok']
        assert 'line1' in ''.join(data['lines'])
    except TypeError:
        # Fallback - call the helper directly
        fake_req = type('R', (), {'headers': {'X-Admin-Key': 'secret123'}})()
        resp = sentinel_mod._read_audit_log(fake_req, 'test_audit.log')
        assert resp.status_code == 200
        data = resp.json()
        assert data['ok']
        assert 'line1' in ''.join(data['lines'])
