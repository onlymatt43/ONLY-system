#!/usr/bin/env python3
"""
E2E-style tests for Bunny embed security
"""
import os
import requests

CURATOR_URL = os.environ.get('CURATOR_URL', 'http://localhost:5061')
PUBLIC_URL = os.environ.get('PUBLIC_URL', 'http://localhost:5062')


def test_bunny_allowed_referrers():
    # Get a private video from curator
    r = requests.get(f"{CURATOR_URL}/videos?library=private&limit=1")
    assert r.status_code == 200, "Curator videos endpoint not available"
    videos = r.json()
    if not videos:
        print('No private videos found. Run POST /sync/bunny library=private to populate.')
        return

    video = videos[0]
    bunny_guid = video.get('bunny_video_id')
    lib_id = os.environ.get('BUNNY_PRIVATE_LIBRARY_ID', '389178')

    embed_url = f"https://iframe.mediadelivery.net/embed/{lib_id}/{bunny_guid}"

    # Allowed referer
    allowed = requests.get(embed_url, headers={'Referer': PUBLIC_URL}, timeout=10)
    print('Allowed referer ->', allowed.status_code)
    assert allowed.status_code in (200, 206), 'Allowed referer should be able to access the video'

    # Disallowed referer
    disallowed = requests.get(embed_url, headers={'Referer': 'https://evil.example'}, timeout=10)
    print('Disallowed referer ->', disallowed.status_code)
    assert disallowed.status_code in (401, 403), 'Disallowed referer must be blocked'


def test_api_embed_returns_token_for_private_video():
    r = requests.get(f"{CURATOR_URL}/videos?library=private&limit=1")
    assert r.status_code == 200
    videos = r.json()

    if not videos:
        print('No private videos found.')
        return

    vid = videos[0].get('id')
    r2 = requests.get(f"{PUBLIC_URL}/api/embed/{vid}")
    print('Embed endpoint ->', r2.status_code)
    assert r2.status_code == 200, 'Embed endpoint should return 200 for a private video when the access policy allows it'
    data = r2.json()
    url = data.get('embed_url', '')
    assert 'token=' in url or 'expires=' in url, 'Signed token should be present for private video'
