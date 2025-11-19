#!/usr/bin/env python3
"""
Test direct des URLs Bunny pour diagnostiquer 403
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

BUNNY_SECURITY_KEY = os.environ.get('BUNNY_SECURITY_KEY')

# URLs à tester
test_urls = {
    "iframe_sans_token": "https://iframe.mediadelivery.net/embed/389178/85e41419-5b46-4db9-ba15-32c86aa08032",
    "iframe_avec_autoplay": "https://iframe.mediadelivery.net/embed/389178/85e41419-5b46-4db9-ba15-32c86aa08032?autoplay=true",
}

print("🧪 Test des URLs Bunny Stream")
print("=" * 60)
print(f"Security Key configurée: {'✅ OUI' if BUNNY_SECURITY_KEY else '❌ NON'}")
print()

for name, url in test_urls.items():
    print(f"Testing: {name}")
    print(f"URL: {url}")
    
    try:
        # Test avec différents headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Referer': 'https://only-public.onrender.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 403:
            print(f"❌ 403 FORBIDDEN")
            print(f"Headers reçus: {dict(response.headers)}")
            print(f"Body: {response.text[:200]}")
        elif response.status_code == 200:
            print(f"✅ 200 OK - La vidéo est accessible")
        else:
            print(f"⚠️ Status inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("-" * 60)
    print()

# Test Bunny API
print("🔍 Test Bunny API (vérifier que vidéo existe)")
api_url = "https://video.bunnycdn.com/library/389178/videos/85e41419-5b46-4db9-ba15-32c86aa08032"
api_key = os.environ.get('BUNNY_PRIVATE_API_KEY')

if api_key:
    try:
        headers = {'AccessKey': api_key}
        response = requests.get(api_url, headers=headers, timeout=10)
        
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            video = response.json()
            print(f"✅ Vidéo existe: {video.get('title', 'N/A')}")
            print(f"Status: {video.get('status', 'N/A')}")
            print(f"Availability: {video.get('availabilityStatus', 'N/A')}")
        else:
            print(f"❌ API error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Erreur API: {e}")
else:
    print("⚠️ BUNNY_PRIVATE_API_KEY non configurée")

print()
print("=" * 60)
print("💡 Prochaine étape basée sur résultats ci-dessus")
