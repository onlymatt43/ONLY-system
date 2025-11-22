#!/usr/bin/env python3
"""Safe helper to verify Bunny signed embed URL on the host where the
BUNNY_SECURITY_KEY is set (run in production). This script will:

- Read environment variables (BUNNY_SECURITY_KEY, BUNNY_PRIVATE_LIBRARY_ID,
  BUNNY_PUBLIC_LIBRARY_ID).
- Generate a signed embed URL using the canonical format and the server-side
  signer (doesn't print the secret).
- Optionally probe the embed URL (HEAD request) and report HTTP status.

Usage (run on host where env vars are configured):
  python scripts/verify_bunny_embed.py --video-id <VIDEO_ID> --library private --probe

Important: the script never echoes the secret key. It prints token metadata
and whether the embed endpoint returns 200/403.
"""

import os
import argparse
import urllib.parse as up
import requests
from public_interface.bunny_signer import get_secure_embed_url


def mask_token(token: str) -> str:
    if not token:
        return '<missing>'
    if len(token) <= 8:
        return token
    return token[:4] + '...' + token[-4:]


def main():
    parser = argparse.ArgumentParser(description='Verify Bunny signed embed URL (run on server)')
    parser.add_argument('--video-id', required=True, help='Bunny video id/guid')
    parser.add_argument('--library', choices=['private', 'public'], default='private')
    parser.add_argument('--expires-hours', type=int, default=2, help='Expiry hours for generated token')
    parser.add_argument('--probe', action='store_true', help='Perform an HTTP HEAD request to the generated embed URL')
    parser.add_argument('--autoplay', action='store_true', help='Include autoplay flag in URL')
    args = parser.parse_args()

    security_key = os.environ.get('BUNNY_SECURITY_KEY')
    private_id = os.environ.get('BUNNY_PRIVATE_LIBRARY_ID')
    public_id = os.environ.get('BUNNY_PUBLIC_LIBRARY_ID')

    if args.library == 'private':
        library_id = int(private_id) if private_id else None
    else:
        library_id = int(public_id) if public_id else None

    if library_id is None:
        print('ERROR: Missing library id in environment variables')
        return 2

    # Generate signed URL using local key (no key printed)
    url = get_secure_embed_url(library_id=library_id, video_id=args.video_id, security_key=security_key, expires_in_hours=args.expires_hours, autoplay=args.autoplay)

    # Parse token / expires from url for inspection
    q = up.urlparse(url).query
    params = dict([p.split('=', 1) for p in q.split('&') if '=' in p]) if q else {}
    token = params.get('token')
    expires = params.get('expires')

    print('\n--- Bunny Embed Verification ---')
    print('video_id       :', args.video_id)
    print('library         :', args.library)
    print('library_id      :', library_id)
    print('token present   :', bool(token))
    print('token (masked)  :', mask_token(token))
    print('expires         :', expires)

    if args.probe:
        try:
            # HEAD is safer and avoids downloading media content
            r = requests.head(url, allow_redirects=True, timeout=10)
            print(f'probe status    : {r.status_code} {r.reason}')
            if r.status_code == 200:
                print('embed reachable: OK (200)')
                return 0
            elif r.status_code == 403:
                print('embed reachable: Forbidden (403) - likely token/allowed-referrer mismatch')
                return 3
            else:
                print('embed probe returned:', r.status_code)
                return 4
        except Exception as e:
            print('probe failed:', e)
            return 5
    else:
        print('\nNote: run with --probe to perform an HTTP HEAD check against the embed URL')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
