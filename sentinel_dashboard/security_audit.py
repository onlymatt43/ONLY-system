"""
Security Audit - Teste les failles de sécurité vidéo
"""

import requests

def test_video_security():
    """Teste si les vidéos sont réellement protégées"""
    
    print("\n🔒 AUDIT DE SÉCURITÉ VIDÉO")
    print("=" * 60)
    
    # Test 1: Page /watch accessible sans token?
    print("\n[Test 1] Page /watch accessible sans auth?")
    response = requests.get("https://only-public.onrender.com/watch/121")
    if response.status_code == 200:
        # Check si iframe dans HTML
        if "iframe.mediadelivery.net" in response.text:
            print("  ❌ FAIL: iframe Bunny visible dans HTML")
            print("  → Quelqu'un peut copier l'URL iframe")
            
            # Extract iframe URL
            import re
            iframe_match = re.search(r'src="(https://iframe\.mediadelivery\.net/[^"]+)"', response.text)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                print(f"  → URL trouvée: {iframe_url[:80]}...")
                
                # Test 2: iframe accessible depuis autre domaine?
                print("\n[Test 2] iframe accessible depuis n'importe quel site?")
                iframe_response = requests.get(iframe_url, headers={"Referer": "https://hacksite.com"})
                if iframe_response.status_code == 200:
                    print("  ❌ FAIL: iframe accessible depuis n'importe quel domaine")
                    print("  → Vidéo peut être embedée partout!")
                elif iframe_response.status_code == 403:
                    print("  ✅ PASS: Bunny bloque domaines non-autorisés")
                else:
                    print(f"  ⚠️  Status: {iframe_response.status_code}")
        else:
            print("  ✅ PASS: Pas d'iframe dans HTML")
    else:
        print(f"  ✅ PASS: Page bloquée ({response.status_code})")
    
    # Test 3: HLS URLs directes accessibles?
    print("\n[Test 3] URLs HLS directes accessibles?")
    hls_url = "https://vz-a3ab0733-842.b-cdn.net/85e41419-5b46-4db9-ba15-32c86aa08032/playlist.m3u8"
    hls_response = requests.get(hls_url)
    if hls_response.status_code == 200:
        print("  ❌ FAIL: URLs HLS accessibles directement")
        print("  → Quelqu'un peut télécharger la vidéo!")
    elif hls_response.status_code == 403:
        print("  ✅ PASS: URLs HLS bloquées")
    else:
        print(f"  ⚠️  Status: {hls_response.status_code}")
    
    # Test 4: API /api/videos accessible sans token?
    print("\n[Test 4] API vidéos accessible sans auth?")
    api_response = requests.get("https://only-public.onrender.com/api/videos")
    if api_response.status_code == 200:
        videos = api_response.json()
        vip_videos = [v for v in videos if v.get("access_level") == "vip"]
        if vip_videos:
            print(f"  ⚠️  {len(vip_videos)} vidéos VIP dans API publique")
            print("  → Quelqu'un peut voir les metadata (titres, IDs)")
        else:
            print("  ✅ PASS: Seulement vidéos publiques dans API")
    else:
        print(f"  Status: {api_response.status_code}")
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    return {
        "page_access": "FAIL" if "iframe.mediadelivery.net" in response.text else "PASS",
        "hls_blocked": "PASS" if hls_response.status_code == 403 else "FAIL",
    }

if __name__ == "__main__":
    results = test_video_security()
    
    print("\n🎯 RECOMMANDATIONS:")
    print("1. ✅ HLS URLs sont bloquées (403)")
    print("2. ❌ Iframe visible dans HTML même sans token")
    print("3. ❌ Page /watch accessible (devrait redirect si pas auth)")
    print("\n💡 SOLUTIONS:")
    print("- Option A: Activer Bunny Token Auth + signed URLs")
    print("- Option B: Bloquer page /watch si pas de token")
    print("- Option C: Les deux (recommandé)")
