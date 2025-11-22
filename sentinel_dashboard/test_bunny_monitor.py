import os
import tempfile
from sentinel_dashboard.sentinel import SentinelMonitor


def test_perform_bunny_checks(monkeypatch, tmp_path):
    # Setup env
    monkeypatch.setenv('BUNNY_PRIVATE_LIBRARY_ID', '111')
    monkeypatch.setenv('BUNNY_SECURITY_KEY', 'abc123')
    monkeypatch.setenv('SENTINEL_BUNNY_TEST_VIDEOS', 'vidA,vidB')

    # fake signer
    def fake_signed(library_id, video_id, security_key=None, expires_in_hours=2, autoplay=True):
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?token=MOCK&expires=999"

    monkeypatch.setattr('public_interface.bunny_signer.get_secure_embed_url', fake_signed)

    # fake HEAD probe returning 200 for vidA, 403 for vidB
    class Dummy200:
        status_code = 200
    class Dummy403:
        status_code = 403

    def fake_head(url, timeout=None, allow_redirects=True):
        if 'vidA' in url:
            return Dummy200()
        return Dummy403()

    monkeypatch.setattr('requests.head', fake_head)

    monitor = SentinelMonitor()
    monitor.bunny_videos = ['vidA', 'vidB']

    results = monitor.perform_bunny_checks()
    assert isinstance(results, list)
    assert any(r['video'] == 'vidA' and r['probe_ok'] is True for r in results)
    assert any(r['video'] == 'vidB' and r['probe_ok'] is False for r in results)

    # ensure audit log was written
    log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'sentinel_actions.log')
    assert os.path.exists(log_path)
    content = open(log_path, 'r', encoding='utf-8').read()
    assert 'bunny_check' in content
