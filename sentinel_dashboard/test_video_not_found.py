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


def test_auto_fix_video_not_found_with_empty_db(monkeypatch):
    # Simulate Curator /videos/134 404, empty listing, and successful sync followed by video present
    calls = {"seq": []}

    class DummyNotFound:
        status_code = 404
        text = '{"detail":"Video 134 not found"}'

    class DummyEmptyList:
        status_code = 200
        def json(self):
            return []

    class DummySyncResp:
        status_code = 200
        def json(self):
            return {"ok": True, "total_synced": 1, "details": {"private": 1}}

    class DummyNowFound:
        status_code = 200
        def json(self):
            return {"id": 134, "bunny_video_id": "guid-134"}

    def fake_get(url, timeout=None, **kwargs):
        # Sequence of GETs inside _fix_video_not_found
        # 1) GET /videos/134 -> 404
        # 2) GET /videos?limit=1 -> []
        # 3) re-check GET /videos/134 -> 200
        seq = len(calls["seq"])
        calls["seq"].append(url)
        if seq == 0:
            return DummyNotFound()
        if seq == 1:
            return DummyEmptyList()
        return DummyNowFound()

    def fake_post(url, timeout=None, **kwargs):
        return DummySyncResp()

    monkeypatch.setenv('SENTINEL_WATCH_TEST_VIDEO_ID', '134')
    monkeypatch.setenv('SENTINEL_AUTO_FIX_VIDEO_NOT_FOUND', 'true')
    monkeypatch.setenv('PUBLIC_URL', 'https://only-public.onrender.com')
    monkeypatch.setenv('CURATOR_URL', 'https://only-curator.onrender.com')
    monkeypatch.setattr('requests.get', fake_get)
    monkeypatch.setattr('requests.post', fake_post)

    autofix = SentinelAutoFix()
    fix = autofix._fix_video_not_found()
    assert fix is not None
    assert fix.get('auto_fixed') is True
    assert 'became available' in fix.get('message', '')
