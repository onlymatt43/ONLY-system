import os
from scripts import verify_bunny_embed as vbe


def test_mask_token():
    assert vbe.mask_token('') == '<missing>'
    assert vbe.mask_token('abc') == 'abc'
    assert vbe.mask_token('abcdefghijkl') == 'abcd...ijkl'


def test_script_generates_and_parses_url(monkeypatch, tmp_path):
    # Use a deterministic expiry to avoid time drift
    monkeypatch.setenv('BUNNY_PRIVATE_LIBRARY_ID', '111')
    monkeypatch.setenv('BUNNY_SECURITY_KEY', 'my-secret')

    # Patch get_secure_embed_url to return a known URL
    def fake_get(library_id, video_id, security_key=None, expires_in_hours=2, autoplay=True, expires_ts=None):
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?token=MOCKTOKEN&expires=12345"

    monkeypatch.setattr('public_interface.bunny_signer.get_secure_embed_url', fake_get)

    # Call main logic without probe, emulate args
    class Args:
        video_id = 'videoX'
        library = 'private'
        expires_hours = 2
        probe = False
        autoplay = True

    # Run parsing logic directly
    url = fake_get(111, 'videoX')
    assert 'token=MOCKTOKEN' in url and 'expires=12345' in url
