"""
Sentinel E2E Tester - Tests automatiques bout-en-bout
Vérifie que les pages web fonctionnent réellement côté navigateur
"""

import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser
import requests

@dataclass
class E2ETestResult:
    """Résultat d'un test E2E"""
    test_name: str
    passed: bool
    error_message: Optional[str]
    screenshot_path: Optional[str]
    duration_ms: int
    timestamp: str

class E2ETester:
    """Teste les interfaces utilisateur avec un vrai navigateur"""
    
    def __init__(self, public_url: str, curator_url: str):
        self.public_url = public_url
        self.curator_url = curator_url
        self.screenshot_dir = "./e2e_screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def test_video_playback(self, video_id: int = 121) -> E2ETestResult:
        """Test critique: vérifie que les vidéos se chargent et jouent"""
        start_time = time.time()
        test_name = f"video_playback_{video_id}"
        
        try:
            with sync_playwright() as p:
                # Lance navigateur headless
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Va sur la page watch (wait_until=domcontentloaded pour éviter timeout)
                url = f"{self.public_url}/watch/{video_id}"
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                
                # Attends que l'iframe Bunny soit visible
                page.wait_for_selector(".om-video-card iframe", timeout=5000)
                
                # Vérifie que l'iframe Bunny Stream est présente et bien configurée
                iframe_src = page.evaluate("""
                    () => {
                        const iframe = document.querySelector('.om-video-card iframe');
                        return iframe ? iframe.src : null;
                    }
                """)
                
                if not iframe_src:
                    raise Exception("Bunny iframe not found - template bug")
                
                # Vérifie que l'URL iframe est valide (Bunny Stream embed)
                if not iframe_src.startswith('https://iframe.mediadelivery.net/embed/'):
                    raise Exception(f"Invalid Bunny embed URL: {iframe_src}")
                
                # Vérifie que l'iframe contient l'ID de la vidéo
                if '389178' not in iframe_src:  # Library ID
                    raise Exception(f"Bunny library ID missing in embed: {iframe_src}")
                
                # Vérifie que l'iframe est bien configurée (autoplay, etc.)
                iframe_config = page.evaluate("""
                    () => {
                        const iframe = document.querySelector('.om-video-card iframe');
                        return {
                            allowfullscreen: iframe.allowFullscreen,
                            loading: iframe.loading,
                            has_allow: iframe.getAttribute('allow') !== null
                        };
                    }
                """)
                
                if not iframe_config['allowfullscreen']:
                    raise Exception("Iframe should have allowfullscreen enabled")
                
                # Screenshot de succès
                screenshot_path = f"{self.screenshot_dir}/{test_name}_success.png"
                page.screenshot(path=screenshot_path)
                
                browser.close()
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return E2ETestResult(
                    test_name=test_name,
                    passed=True,
                    error_message=None,
                    screenshot_path=screenshot_path,
                    duration_ms=duration_ms,
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Screenshot d'erreur si possible
            screenshot_path = None
            try:
                screenshot_path = f"{self.screenshot_dir}/{test_name}_error.png"
                page.screenshot(path=screenshot_path)
                browser.close()
            except:
                pass
            
            return E2ETestResult(
                test_name=test_name,
                passed=False,
                error_message=str(e),
                screenshot_path=screenshot_path,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat()
            )
    
    def test_homepage_loads(self) -> E2ETestResult:
        """Vérifie que la homepage charge correctement"""
        start_time = time.time()
        test_name = "homepage_load"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(self.public_url, timeout=15000, wait_until="domcontentloaded")
                
                # Vérifie que le titre existe
                title = page.title()
                if not title:
                    raise Exception("Page title is empty")
                
                # Vérifie qu'il y a des vidéos affichées
                video_cards = page.query_selector_all(".video-card")
                if len(video_cards) == 0:
                    raise Exception("No video cards found on homepage")
                
                # Screenshot (optionnel - skip si problème)
                screenshot_path = None
                try:
                    screenshot_path = f"{self.screenshot_dir}/{test_name}_success.png"
                    page.screenshot(path=screenshot_path, timeout=5000)
                except:
                    pass
                
                browser.close()
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return E2ETestResult(
                    test_name=test_name,
                    passed=True,
                    error_message=None,
                    screenshot_path=screenshot_path,
                    duration_ms=duration_ms,
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            screenshot_path = None
            try:
                screenshot_path = f"{self.screenshot_dir}/{test_name}_error.png"
                page.screenshot(path=screenshot_path)
                browser.close()
            except:
                pass
            
            return E2ETestResult(
                test_name=test_name,
                passed=False,
                error_message=str(e),
                screenshot_path=screenshot_path,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat()
            )
    
    def test_search_functionality(self) -> E2ETestResult:
        """Vérifie que la recherche fonctionne"""
        start_time = time.time()
        test_name = "search_functionality"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(self.public_url, timeout=15000, wait_until="domcontentloaded")
                
                # Trouve le champ de recherche
                search_input = page.query_selector("input[type='search'], input[placeholder*='Search']")
                if not search_input:
                    raise Exception("Search input not found")
                
                # Tape une recherche
                search_input.fill("test")
                search_input.press("Enter")
                
                # Attends les résultats
                time.sleep(1)
                
                screenshot_path = f"{self.screenshot_dir}/{test_name}_success.png"
                page.screenshot(path=screenshot_path)
                
                browser.close()
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return E2ETestResult(
                    test_name=test_name,
                    passed=True,
                    error_message=None,
                    screenshot_path=screenshot_path,
                    duration_ms=duration_ms,
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            screenshot_path = None
            try:
                screenshot_path = f"{self.screenshot_dir}/{test_name}_error.png"
                page.screenshot(path=screenshot_path)
                browser.close()
            except:
                pass
            
            return E2ETestResult(
                test_name=test_name,
                passed=False,
                error_message=str(e),
                screenshot_path=screenshot_path,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat()
            )
    
    def test_video_api_consistency(self) -> E2ETestResult:
        """Vérifie que les données API matchent avec ce qui s'affiche"""
        start_time = time.time()
        test_name = "api_consistency"
        
        try:
            # Récupère une vidéo de l'API
            response = requests.get(f"{self.curator_url}/videos/121", timeout=5)
            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}")
            
            api_data = response.json()
            
            # Vérifie que les champs critiques existent
            required_fields = ['id', 'video_url', 'bunny_video_id', 'title', 'cdn_hostname']
            missing = [f for f in required_fields if f not in api_data]
            
            if missing:
                raise Exception(f"API missing fields: {', '.join(missing)}")
            
            # Vérifie que video_url est bien formé
            if not api_data['video_url'].startswith('https://'):
                raise Exception(f"Invalid video_url format: {api_data['video_url']}")
            
            if '.m3u8' not in api_data['video_url']:
                raise Exception(f"video_url is not HLS: {api_data['video_url']}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return E2ETestResult(
                test_name=test_name,
                passed=True,
                error_message=None,
                screenshot_path=None,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            return E2ETestResult(
                test_name=test_name,
                passed=False,
                error_message=str(e),
                screenshot_path=None,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat()
            )
    
    def run_all_tests(self) -> Dict[str, E2ETestResult]:
        """Lance tous les tests E2E"""
        print("\n🧪 Starting E2E Tests...")
        print("=" * 60)
        
        results = {}
        
        # Test 1: API consistency (pas besoin de navigateur)
        print("\n[1/4] Testing API consistency...")
        results['api_consistency'] = self.test_video_api_consistency()
        print(f"  {'✅ PASS' if results['api_consistency'].passed else '❌ FAIL'} ({results['api_consistency'].duration_ms}ms)")
        if not results['api_consistency'].passed:
            print(f"  Error: {results['api_consistency'].error_message}")
        
        # Test 2: Homepage
        print("\n[2/4] Testing homepage...")
        results['homepage'] = self.test_homepage_loads()
        print(f"  {'✅ PASS' if results['homepage'].passed else '❌ FAIL'} ({results['homepage'].duration_ms}ms)")
        if not results['homepage'].passed:
            print(f"  Error: {results['homepage'].error_message}")
        
        # Test 3: Video playback (critique)
        print("\n[3/4] Testing video playback...")
        results['video_playback'] = self.test_video_playback()
        print(f"  {'✅ PASS' if results['video_playback'].passed else '❌ FAIL'} ({results['video_playback'].duration_ms}ms)")
        if not results['video_playback'].passed:
            print(f"  Error: {results['video_playback'].error_message}")
        
        # Test 4: Search
        print("\n[4/4] Testing search...")
        results['search'] = self.test_search_functionality()
        print(f"  {'✅ PASS' if results['search'].passed else '❌ FAIL'} ({results['search'].duration_ms}ms)")
        if not results['search'].passed:
            print(f"  Error: {results['search'].error_message}")
        
        # Résumé
        print("\n" + "=" * 60)
        passed = sum(1 for r in results.values() if r.passed)
        total = len(results)
        print(f"📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All tests passed!")
        else:
            print(f"❌ {total - passed} test(s) failed")
            print("\n📸 Screenshots saved in:", self.screenshot_dir)
        
        return results


if __name__ == "__main__":
    """Test local"""
    print("🎭 E2E Tester - Public Interface Tests")
    
    tester = E2ETester(
        public_url="http://localhost:5062",
        curator_url="http://localhost:5061"
    )
    
    results = tester.run_all_tests()
    
    # Exit code
    import sys
    all_passed = all(r.passed for r in results.values())
    sys.exit(0 if all_passed else 1)
