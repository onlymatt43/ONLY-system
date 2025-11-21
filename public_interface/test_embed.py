#!/usr/bin/env python3
"""
Integration tests for /api/embed endpoint - flow verification
"""
import requests
import os
import json

CURATOR_URL = os.environ.get('CURATOR_URL', 'http://localhost:5061')
PUBLIC_URL = os.environ.get('PUBLIC_URL', 'http://localhost:5062')

# Pick a sample video id from curator (must be present)
try:
    videos = requests.get(f"{CURATOR_URL}/videos?limit=1").json()
    sample = videos[0]
    sample_id = sample.get('id')
    print('Sample video:', sample)
except Exception as e:
    print('Unable to fetch sample video from Curator:', e)
    sample_id = None

if sample_id:
    r = requests.get(f"{PUBLIC_URL}/api/embed/{sample_id}")
    print('Embed endpoint status:', r.status_code)
    print('Response:', r.text)
else:
    print('No sample video found - try running POST /sync/bunny first')
