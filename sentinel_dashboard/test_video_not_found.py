import os
from sentinel_dashboard.sentinel import SentinelAutoFix


def test_detect_video_not_found(monkeypatch):
    # Simulate public watch page returning JSON detail for a missing video
    class DummyResp:
        status_code = 404
        text = '{"detail":"Video 134 not found"}'

    def fake_get(url, timeout=None):
        return DummyResp()

    monkeypatch.setenv('SENTINEL_WATCH_TEST_VIDEO_ID', '134')
    monkeypatch.setenv('PUBLIC_URL', 'https://only-public.onrender.com')
    monkeypatch.setattr('requests.get', fake_get)

    autofix = SentinelAutoFix()
    issue = autofix._check_video_403()
    assert issue is not None
    assert issue.get('type') == 'VIDEO_NOT_FOUND'
    assert '134' in issue.get('message', '') or 'not found' in issue.get('details', '')
