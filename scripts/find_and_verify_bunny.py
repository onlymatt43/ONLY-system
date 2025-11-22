#!/usr/bin/env python3
"""Find a place where Bunny env values are present and run the safe verifier.

Search order (examples):
 - current environment variables
 - repo root .env
 - service .env files: public_interface/.env, monetizer_ai/.env, web_interface/.env, sentinel_dashboard/.env.prod
 - docker-compose.yml env_file entries (if present)

The script never prints the secret value. It will show masked token, and can run a HEAD probe to check Bunny response.

Usage:
  python scripts/find_and_verify_bunny.py --video-id <ID> [--library private|public] [--probe]

This script is safe to run on the host that stores the production environment variables.
"""

from __future__ import annotations

import argparse
import os
import re
from typing import Dict, Optional, Tuple, List
import pathlib
import configparser
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def find_env_in_file(path: pathlib.Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    data = {}
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        return {}

    # Simple .env style parse: KEY=VALUE, ignore comments and empty lines
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            v = v.strip().strip('"').strip("'")
            data[k.strip()] = v
    return data


def masked(v: Optional[str]) -> str:
    if not v:
        return '<missing>'
    if len(v) <= 8:
        return v
    return v[:4] + '...' + v[-4:]


def find_candidate_envs() -> List[Tuple[str, Dict[str, str]]]:
    """Return list of (source-name, env-dict) candidates found.

    Order prefers current os.environ, then repository-level .env, then service-specific files.
    """
    found = []

    # 1) Current process env
    current = {k: v for k, v in os.environ.items() if k.startswith('BUNNY_')}
    if current:
        found.append(('process-environment', current))

    # 2) repo root .env
    root_env = REPO_ROOT / '.env'
    d = find_env_in_file(root_env)
    if any(k.startswith('BUNNY_') for k in d):
        found.append((str(root_env), d))

    # 3) service env files
    candidates = [
        REPO_ROOT / 'public_interface' / '.env',
        REPO_ROOT / 'monetizer_ai' / '.env',
        REPO_ROOT / 'web_interface' / '.env',
        REPO_ROOT / 'sentinel_dashboard' / '.env.prod',
        REPO_ROOT / 'docker-compose.yml',
        REPO_ROOT / '.env Global'
    ]

    for p in candidates:
        if p.suffix == '.yml' or p.suffix == '.yaml':
            # quick scan for env_file: or BUNNY_SECURITY_KEY inline
            try:
                txt = p.read_text(encoding='utf-8')
            except Exception:
                continue
            if 'BUNNY_SECURITY_KEY' in txt or 'env_file' in txt:
                # parse any env_file lines to check referenced files
                envs = {}
                # collect env_file values
                for m in re.finditer(r'env_file:\s*(.*)', txt):
                    candidate = (p.parent / m.group(1).strip()).resolve()
                    envs.update(find_env_in_file(candidate))
                # also include inline declaration
                envs.update({k: v for k, v in [ln.split('=',1) for ln in txt.splitlines() if '=' in ln and ln.strip().startswith('BUNNY_')]} if 'BUNNY_' in txt else {})
                if any(k.startswith('BUNNY_') for k in envs):
                    found.append((str(p), envs))
        else:
            d = find_env_in_file(p)
            if any(k.startswith('BUNNY_') for k in d):
                found.append((str(p), d))

    return found


def run_verify_with_env(env_source: str, env_vars: Dict[str, str], opts: argparse.Namespace) -> int:
    """Run verification logic with the provided env vars overlaying os.environ.

    Uses the existing safe script functionality inside this repository (public_interface.bunny_signer, requests).
    """
    # Prepare merged environment for the subprocess
    merged_env = os.environ.copy()
    merged_env.update(env_vars)

    # We'll import the module here and call the helper directly for safety
    from public_interface.bunny_signer import get_secure_embed_url
    import requests

    lib_key_name = 'BUNNY_PRIVATE_LIBRARY_ID' if opts.library == 'private' else 'BUNNY_PUBLIC_LIBRARY_ID'
    if lib_key_name not in merged_env:
        print(f"selected source {env_source} doesn't contain {lib_key_name} — skipping")
        return 3

    library_id = int(merged_env.get(lib_key_name))
    key = merged_env.get('BUNNY_SECURITY_KEY')

    print('\n=== Selected env: {} ==='.format(env_source))
    print('library_id:', library_id)
    print('secret present:', bool(key))
    print('masked secret :', masked(key))

    # Generate signed url via server-side signer (it won't print the secret)
    signed_url = get_secure_embed_url(library_id=library_id, video_id=opts.video_id, security_key=key, expires_in_hours=opts.expires_hours, autoplay=opts.autoplay)

    print('\nGenerated signed URL:')
    # Print URL but mask token value for safety
    if 'token=' in signed_url:
        parts = signed_url.split('?')
        base = parts[0]
        qs = parts[1] if len(parts) > 1 else ''
        params = dict([p.split('=',1) for p in qs.split('&') if '=' in p])
        token = params.get('token')
        expires = params.get('expires')
        print(f"{base}?token={masked(token)}&expires={expires}")
    else:
        print(signed_url)

    if opts.probe:
        print('\nProbing URL (HEAD request) — the request is performed from THIS host')
        try:
            r = requests.head(signed_url, timeout=10, allow_redirects=True)
            print('Probe result:', r.status_code, r.reason)
            if r.status_code == 200:
                print('OK — Bunny accepted the request (200)')
                return 0
            if r.status_code == 403:
                print('Forbidden — likely token / allowed-referrers mismatch (403)')
                return 2
            print('Other probe status:', r.status_code)
            return 4
        except Exception as e:
            print('Probe failed:', e)
            return 5

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Find env and verify Bunny embed URL across candidates')
    parser.add_argument('--video-id', required=True)
    parser.add_argument('--library', choices=['private', 'public'], default='private')
    parser.add_argument('--probe', action='store_true', help='HEAD probe the generated URL')
    parser.add_argument('--expires-hours', type=int, default=2)
    parser.add_argument('--autoplay', action='store_true')

    opts = parser.parse_args()

    candidates = find_candidate_envs()
    if not candidates:
        print('No candidate envs found. Check that BUNNY_SECURITY_KEY and library IDs exist in env or .env files.')
        return 1

    # Display brief list to user and pick best match
    print('Found candidate sources:')
    for i, (src, env) in enumerate(candidates):
        has_key = 'BUNNY_SECURITY_KEY' in env
        has_lib = ('BUNNY_PRIVATE_LIBRARY_ID' in env) or ('BUNNY_PUBLIC_LIBRARY_ID' in env)
        print(f'  [{i}] {src}  key_present={has_key} lib_present={has_lib}')

    # Prefer process env if present and contains secret + requested library
    preferred = None
    for src, env in candidates:
        if src == 'process-environment':
            if 'BUNNY_SECURITY_KEY' in env and (('BUNNY_PRIVATE_LIBRARY_ID' in env) or ('BUNNY_PUBLIC_LIBRARY_ID' in env)):
                preferred = (src, env)
                break

    if preferred is None:
        # pick first candidate that has BUNNY_SECURITY_KEY and the chosen library id
        for src, env in candidates:
            if 'BUNNY_SECURITY_KEY' in env and (('BUNNY_PRIVATE_LIBRARY_ID' in env) or ('BUNNY_PUBLIC_LIBRARY_ID' in env)):
                preferred = (src, env)
                break

    if preferred is None:
        print('No candidate contained both BUNNY_SECURITY_KEY and a library id — falling back to first candidate')
        preferred = candidates[0]

    src, env = preferred
    return run_verify_with_env(src, env, opts)


if __name__ == '__main__':
    raise SystemExit(main())
