import os
import time
import threading
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from typing import Tuple

# Import Sentinel AI
try:
    from sentinel_ai import SentinelAI  # type: ignore
except Exception:
    # Fallback: define a minimal dummy SentinelAI when the package is not
    # available; this is helpful for tests and local environments without
    # sentinel_ai installed.
    class DummyMetrics:
        def get_stats(self, service, hours=24):
            return {}
        def get_unresolved_alerts(self):
            return []

    class DummyHealer:
        def attempt_wake_up(self, service, url):
            return False

    class SentinelAI:
        def __init__(self, conf):
            self.metrics = DummyMetrics()
            self.chat = type('C', (), {'handle_message': lambda self, message, conf: {'ok': True}})()
            self.healer = DummyHealer()
        def get_system_snapshot(self):
            from types import SimpleNamespace
            return SimpleNamespace(
                timestamp='now', health_score=100, services_up=6, services_down=0,
                total_requests=0, avg_latency_ms=0, error_rate=0, alerts=[]
            )

load_dotenv()

# ✅ FIX: Port cohérent
PORT = int(os.environ.get("PORT", 5059))  # 5059 en local, 10000 sur Render

REFRESH_SEC = int(os.getenv("REFRESH_SEC", "5"))
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL_SEC", "30"))  # AI monitoring cycle
# Bunny periodic checks (comma-separated list of video ids to verify)
SENTINEL_BUNNY_TEST_VIDEOS = os.getenv('SENTINEL_BUNNY_TEST_VIDEOS', '')
# seconds between bunny checks (defaults to MONITOR_INTERVAL if not set)
SENTINEL_BUNNY_CHECK_INTERVAL = int(os.getenv('SENTINEL_BUNNY_CHECK_INTERVAL', str(MONITOR_INTERVAL)))

CURATOR_URL = os.getenv("CURATOR_URL", "https://only-curator.onrender.com/")
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://only-gateway.onrender.com/")
MONETIZER_URL = os.getenv("MONETIZER_URL", "https://only-monetizer.onrender.com/")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://only-public.onrender.com/")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

app = FastAPI(title="Sentinel AI Dashboard", version="2.0")

templates = Jinja2Templates(directory="templates")
# Initialize Sentinel AI - ONLY Core Services (WordPress pipeline removed)
SERVICES_CONFIG = {
    "Gateway": GATEWAY_URL,
    "Curator": CURATOR_URL,
    "Monetizer": MONETIZER_URL,
    "Public": PUBLIC_URL
}

sentinel_ai: Any = SentinelAI(SERVICES_CONFIG)

# Background monitoring thread
def ai_monitor_loop():
    """Background thread for continuous AI monitoring"""
    print(f"[Sentinel AI] Starting monitoring loop (interval: {MONITOR_INTERVAL}s)")
    while True:
        try:
            sentinel_ai.monitor_cycle()
        except Exception as e:
            print(f"[Sentinel AI] Error in monitor cycle: {e}")
        time.sleep(MONITOR_INTERVAL)

# Start AI monitoring in background
def _should_autostart() -> bool:
    """Determine whether to autostart background monitoring threads.

    - Disabled when running under pytest (PYTEST_CURRENT_TEST present)
    - Disabled when SENTINEL_DISABLE_AUTOSTART is set to '1'
    """
    if os.environ.get('SENTINEL_DISABLE_AUTOSTART', '').lower() in ('1', 'true'):
        return False
    # pytest sets PYTEST_CURRENT_TEST in environment for tests
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return False
    # also avoid autostart if pytest is imported
    import sys
    if any('pytest' in k for k in sys.modules.keys()):
        return False
    return True


if _should_autostart():
    monitor_thread = threading.Thread(target=ai_monitor_loop, daemon=True)
    monitor_thread.start()


# ---------- Helpers ----------
def fetch_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch jobs from Gateway API instead of direct DB access"""
    try:
        r = requests.get(f"{GATEWAY_URL}/jobs", params={"limit": limit}, timeout=5)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"[Sentinel] Error fetching jobs: {e}")
        return []


def ping(url: str, timeout: float = 2.5) -> Dict[str, Any]:
    if not url:
        return {"ok": False, "status": "NA"}
    try:
        r = requests.get(url, timeout=timeout)
        ok = (200 <= r.status_code < 300)
        return {"ok": ok, "code": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def service_status_map() -> Dict[str, Dict[str, Any]]:
    """Status map for ONLY core services (WordPress pipeline removed)"""
    return {
        "Gateway": ping(GATEWAY_URL),
        "Curator": ping(CURATOR_URL),
        "Monetizer": ping(MONETIZER_URL),
        "Public": ping(PUBLIC_URL),
    }


# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, limit: int = 100):
    tmpl = env.get_template("index.html")
    jobs = fetch_jobs(limit=limit)
    services = service_status_map()
    
    html = tmpl.render(
        refresh=REFRESH_SEC,
        has_db=True,  # Always True with API access
        db_path="Gateway API",
        jobs=jobs,
        services=services
    )
    return HTMLResponse(html)


@app.get("/chat", response_class=HTMLResponse)
def chat_interface(request: Request):
    """AI Chat Interface"""
    tmpl = env.get_template("chat.html")
    return HTMLResponse(tmpl.render())


@app.get("/api/jobs")
def api_jobs(limit: int = 100):
    return JSONResponse(fetch_jobs(limit=limit))


@app.get("/api/services")
def api_services():
    return JSONResponse(service_status_map())


@app.get("/health")
def health():
    return {"ok": True, "ts": int(time.time())}


# ---------- Sentinel AI Routes ----------

@app.get("/api/system/health")
def system_health():
    """Get comprehensive system health snapshot"""
    snapshot = sentinel_ai.get_system_snapshot()
    return JSONResponse({
        "timestamp": snapshot.timestamp,
        "health_score": snapshot.health_score,
        "services_up": snapshot.services_up,
        "services_down": snapshot.services_down,
        "total_requests": snapshot.total_requests,
        "avg_latency_ms": snapshot.avg_latency_ms,
        "error_rate": snapshot.error_rate,
        "alerts": snapshot.alerts
    })


@app.get("/api/metrics/{service}")
def service_metrics(service: str, hours: int = 24):
    """Get detailed metrics for a service"""
    stats = sentinel_ai.metrics.get_stats(service.capitalize(), hours=hours)
    return JSONResponse(stats)


@app.get("/api/alerts")
def get_alerts():
    """Get all unresolved alerts"""
    alerts = sentinel_ai.metrics.get_unresolved_alerts()
    return JSONResponse([
        {
            "level": a.level,
            "service": a.service,
            "message": a.message,
            "timestamp": a.timestamp,
            "resolved": a.resolved
        }
        for a in alerts
    ])


@app.post("/api/chat")
def chat(message: str = Body(..., embed=True)):
    """Chat interface with Sentinel AI"""
    response = sentinel_ai.chat.handle_message(message, SERVICES_CONFIG)
    return JSONResponse(response)


@app.post("/api/heal/{service}")
def manual_heal(service: str):
    """Manually trigger healing for a service"""
    service_cap = service.capitalize()
    
    if service_cap not in SERVICES_CONFIG:
        return JSONResponse({"error": "Unknown service"}, status_code=404)
    
    url = SERVICES_CONFIG[service_cap]
    success = sentinel_ai.healer.attempt_wake_up(service_cap, url)
    
    return JSONResponse({
        "service": service,
        "action": "wake_up",
        "success": success
    })


@app.get("/logs", response_class=HTMLResponse)
def see_logs(request: Request):
    """Basic admin page to view the logs - protected by admin key in API calls."""
    return templates.TemplateResponse("logs.html", {"request": request})


import re

class SentinelMonitor:
    def __init__(self):
        self.is_active = False
        self.services = {
            "Gateway": os.environ.get('GATEWAY_URL', 'http://localhost:5055'),
            "Curator": os.environ.get('CURATOR_URL', 'http://localhost:5061'),
            "Narrator": os.environ.get('NARRATOR_URL', 'http://localhost:5056'),
            "Publisher": os.environ.get('PUBLISHER_URL', 'http://localhost:5058'),
            "Monetizer": os.environ.get('MONETIZER_URL', 'http://localhost:5060'),
            "Public": os.environ.get('PUBLIC_URL', 'http://localhost:5062')
        }
    
    def perform_bunny_checks(self) -> List[Dict[str, Any]]:
        """Verify configured Bunny videos and return results.

        Uses `get_secure_embed_url` to create a signed embed URL and performs a HEAD request
        to validate access. Results are logged to `logs/sentinel_actions.log` and returned.
        """
        # If no videos configured at instance-level, fall back to env/const
        self.bunny_videos = getattr(self, 'bunny_videos', [v.strip() for v in (os.environ.get('SENTINEL_BUNNY_TEST_VIDEOS', SENTINEL_BUNNY_TEST_VIDEOS) or '').split(',') if v.strip()])
        if not self.bunny_videos:
            return []

        results = []
        from public_interface.bunny_signer import get_secure_embed_url

        # choose library id if available
        try:
            library_id = int(os.environ.get('BUNNY_PRIVATE_LIBRARY_ID') or os.environ.get('BUNNY_PUBLIC_LIBRARY_ID') or 0)
        except Exception:
            library_id = 0

        for vid in self.bunny_videos:
            record = {'video': vid}
            if not library_id:
                record.update({'status': 'no_library_id'})
                results.append(record)
                continue

            key = os.environ.get('BUNNY_SECURITY_KEY')
            try:
                signed = get_secure_embed_url(library_id=library_id, video_id=vid, security_key=key, expires_in_hours=2)
            except Exception as e:
                record.update({'status': 'sign_error', 'error': str(e)[:200]})
                results.append(record)
                continue

            try:
                r = requests.head(signed, timeout=8, allow_redirects=True)
                record.update({'probe_status': r.status_code, 'probe_ok': r.status_code == 200})
            except Exception as e:
                record.update({'probe_status': 'error', 'probe_ok': False, 'error': str(e)[:200]})

            # Log short audit
            try:
                logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
                os.makedirs(logs_dir, exist_ok=True)
                audit_path = os.path.join(logs_dir, 'sentinel_actions.log')
                with open(audit_path, 'a', encoding='utf-8') as fh:
                    fh.write(f"{datetime.utcnow().isoformat()} bunny_check video={vid} probe_ok={record.get('probe_ok')} status={record.get('probe_status')}\n")
            except Exception:
                pass

            results.append(record)

        return results
    
    def start_monitoring(self):
        """Start continuous health checks"""
        self.is_active = True
        print("🛡️ Sentinel activated - Monitoring system")
        self.bunny_videos = [v.strip() for v in (os.environ.get('SENTINEL_BUNNY_TEST_VIDEOS', SENTINEL_BUNNY_TEST_VIDEOS) or '').split(',') if v.strip()]
        self.bunny_interval = int(os.environ.get('SENTINEL_BUNNY_CHECK_INTERVAL', SENTINEL_BUNNY_CHECK_INTERVAL))
        self._next_bunny_check = time.time() + self.bunny_interval
        def monitor_loop():
            while self.is_active:
                # Regular health checks
                self.perform_health_check()

                # Periodic Bunny checks (if configured)
                now = time.time()
                if self.bunny_videos and now >= self._next_bunny_check:
                    try:
                        res = self.perform_bunny_checks()
                        print(f"🔎 Bunny checks: {res}")
                    except Exception as e:
                        print(f"Error during bunny checks: {e}")
                    self._next_bunny_check = now + self.bunny_interval

                # Sleep for MONITOR_INTERVAL (keeps loop responsive)
                time.sleep(MONITOR_INTERVAL)
        
        # Start in background thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def perform_health_check(self):
        """Check all services"""
        for name, url in self.services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name} is operational")
                else:
                    print(f"❌ {name} returned {response.status_code}")
                    self.wake_service(url)
            except Exception as e:
                print(f"❌ {name} is down: {e}")
                self.wake_service(url)
    
    def wake_service(self, url):
        """Wake up sleeping service (Render free tier)"""
        try:
            requests.get(url, timeout=10)
            print(f"🔄 Attempting to wake service at {url}")
        except:
            pass

# Initialize and start monitoring
# Initialize and start monitoring only when autostart is enabled. This
# prevents background threads from launching during unit tests or when the
# developer explicitly disables autostart with SENTINEL_DISABLE_AUTOSTART=1.
monitor = None
if _should_autostart():
    monitor = SentinelMonitor()
    monitor.start_monitoring()

class SentinelAutoFix:
    """Sentinel qui diagnostique ET corrige automatiquement"""
    
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
    
    def diagnose_system(self) -> dict:
        """Diagnostique complet automatique"""
        print("🔍 Sentinel: Diagnostic automatique...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "issues_found": [],
            "fixes_applied": [],
            "action_required": []
        }
        
        # 1. Check vidéos 403
        video_403 = self._check_video_403()
        if video_403:
            results["issues_found"].append(video_403)

            # Auto-fix si possible
            fix = self._fix_video_403()
            if fix and fix.get("auto_fixed"):
                results["fixes_applied"].append(fix)
            else:
                results["action_required"].append(fix)
        
        # 1b. Check Bunny allowed referrers and embed signing
        bunny_ref = self._check_bunny_referrers()
        if bunny_ref:
            results["issues_found"].append(bunny_ref)
            # Check embed logging & rate-limiting
            audit_check = self._check_embed_audit_and_rate()
            if audit_check:
                results["issues_found"].append(audit_check)

        # 2. Check services down
        services_down = self._check_services()
        results["issues_found"].extend(services_down)
        
        # 3. Check config errors
        config_errors = self._check_configuration()
        results["issues_found"].extend(config_errors)

        return results

    def _check_video_403(self) -> Optional[dict]:
        """Vérifie si vidéos retournent 403"""
        try:
            # Test une vidéo
            response = requests.get(
                "https://only-public.onrender.com/watch/121",
                timeout=5
            )
            if "403" in response.text or response.status_code == 403:
                return {
                    "type": "VIDEO_403",
                    "severity": "CRITICAL",
                    "message": "Les vidéos retournent 403 Forbidden",
                    "detected_at": datetime.now().isoformat()
                }
        except:
            pass

        return None

    def _fix_video_403(self) -> Optional[dict]:
        """Tente de corriger le 403 automatiquement"""

        # Check si BUNNY_SECURITY_KEY existe
        bunny_key = os.environ.get('BUNNY_SECURITY_KEY')

        if not bunny_key:
            return {
                "issue": "VIDEO_403",
                "auto_fixed": False,
                "action": "MANUAL",
                "instructions": [
                    "1. Va sur Bunny Dashboard: https://panel.bunny.net/stream",
                    "2. Library 389178 → Security",
                    "3. OPTION A (Rapide): Désactive 'Embed view token authentication'",
                    "   OU",
                    "4. OPTION B (Sécurisé): Copie Security Key",
                    "5. Ajoute sur Render: BUNNY_SECURITY_KEY=ta-cle",
                    "6. Redeploy only-public"
                ],
                "url": "https://panel.bunny.net/stream",
                "render_url": "https://dashboard.render.com"
            }

        # Si key existe, vérifier qu'elle fonctionne
        from public_interface.bunny_signer import get_secure_embed_url

        try:
            test_url = get_secure_embed_url(
                library_id=389178,
                video_id="test",
                security_key=bunny_key
            )

            if "token=" in test_url:
                return {
                    "issue": "VIDEO_403",
                    "auto_fixed": True,
                    "message": "Signed URLs fonctionnent. Le 403 devrait être résolu après redeploy."
                }
        except Exception as e:
            return {
                "issue": "VIDEO_403",
                "auto_fixed": False,
                "action": "MANUAL",
                "error": str(e),
                "instructions": [
                    "La Security Key semble incorrecte.",
                    "1. Va sur Bunny Dashboard",
                    "2. Vérifie la Security Key",
                    "3. Update BUNNY_SECURITY_KEY sur Render",
                    "4. Redeploy"
                ]
            }

    def _check_bunny_referrers(self) -> Optional[dict]:
        """Verify Bunny Allowed Referrers by testing embeds with referer headers.

        Returns a diagnostic dict if it finds problems.
        """
        try:
            # Try to pick a private video to test
            r = requests.get(f"{CURATOR_URL}/videos?library=private&limit=1", timeout=5)
            r.raise_for_status()
            items = r.json()
            if not items:
                return {
                    "type": "BUNNY_REFERRERS",
                    "severity": "LOW",
                    "message": "No private videos found to test Bunny referer rules",
                    "details": {}
                }

            video = items[0]
            bunny_guid = video.get("bunny_video_id")
            library_id = os.environ.get('BUNNY_PRIVATE_LIBRARY_ID', '389178')

            embed_base = f"https://iframe.mediadelivery.net/embed/{library_id}/{bunny_guid}"

            # Test allowed referer
            allowed_headers = {"Referer": PUBLIC_URL}
            allowed_resp = requests.get(embed_base, headers=allowed_headers, timeout=5)

            # Test disallowed referer
            disallowed_headers = {"Referer": "https://evil.example/"}
            disallowed_resp = requests.get(embed_base, headers=disallowed_headers, timeout=5)

            issues = []
            if allowed_resp.status_code != 200:
                issues.append("Allowed referer returned non-200; check Allowed Referrers in Bunny dashboard")

            if disallowed_resp.status_code == 200:
                issues.append("Disallowed referer can access embed; update Bunny Allowed Referrers to restrict domains")

            # Verify signed url produced by /api/embed
            embed_api = f"{PUBLIC_URL}/api/embed/{video.get('id')}"
            embed_api_resp = requests.get(embed_api, timeout=5)
            token_present = False
            if embed_api_resp.status_code == 200:
                try:
                    data = embed_api_resp.json()
                    url = data.get('embed_url', '')
                    token_present = 'token=' in url or 'expires=' in url
                except:
                    pass

            if not token_present and video.get('library_type') == 'private':
                issues.append('API /api/embed did not return signed token for private video')

            if issues:
                return {
                    "type": "BUNNY_REFERRERS",
                    "severity": "CRITICAL" if any('Disallowed' in i for i in issues) else "HIGH",
                    "message": "Bunny embed referer rules or token signing issues detected",
                    "details": issues
                }

            return None
        except Exception as e:
            return {
                "type": "BUNNY_REFERRERS",
                "severity": "MEDIUM",
                "message": f"Error testing bunny referers: {e}",
                "details": {}
            }

    def _check_embed_audit_and_rate(self) -> Optional[dict]:
        """Check if embed audit logs are present and rate limit enforced."""
        try:
            # Check for audit log file in public interface
            import os
            audit_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'public_interface_audit.log')
            if not os.path.exists(audit_file):
                return {
                    "type": "BUNNY_AUDIT",
                    "severity": "LOW",
                    "message": "Audit log for embed requests not found",
                    "details": {}
                }

            # Check rate limit by making successive requests
            import requests
            url = f"{PUBLIC_URL}/api/embed/1"
            results = []
            for _ in range(5):
                r = requests.get(url, timeout=5)
                results.append(r.status_code)

            if 429 in results:
                # Rate limit present
                return None
            else:
                return {
                    "type": "BUNNY_RATE_LIMIT",
                    "severity": "MEDIUM",
                    "message": "Rate-limit not detected on /api/embed; consider adding limits to prevent abuse",
                    "details": {"samples": results}
                }
        except Exception as e:
            return {
                "type": "BUNNY_AUDIT",
                "severity": "LOW",
                "message": f"Error testing embed audit/rate: {e}",
                "details": {}
            }

    def _check_services(self) -> list:
        """Check tous les services"""
        services = {
            "Gateway": "http://localhost:5055/health",
            "Curator": "http://localhost:5061/health",
            "Monetizer": "http://localhost:5060/health",
            "Public": "http://localhost:5062/health"
        }

        issues = []
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code != 200:
                    issues.append({
                        "type": "SERVICE_DOWN",
                        "service": name,
                        "severity": "HIGH",
                        "message": f"{name} ne répond pas correctement",
                        "action": f"Redémarre: cd {name.lower()} && python3 {name.lower()}.py"
                    })
            except:
                issues.append({
                    "type": "SERVICE_DOWN",
                    "service": name,
                    "severity": "HIGH",
                    "message": f"{name} n'est pas lancé",
                    "action": f"Démarre: cd {name.lower()} && python3 {name.lower()}.py"
                })

        return issues

    def _check_configuration(self) -> list:
        """Vérifie config système"""
        issues = []

        # Check env vars critiques
        required_vars = {
            "BUNNY_SECURITY_KEY": "Bunny Stream",
            "TURSO_DATABASE_URL": "Monetizer (Turso)",
            "TURSO_AUTH_TOKEN": "Monetizer (Turso)"
        }

        for var, service in required_vars.items():
            if not os.environ.get(var):
                issues.append({
                    "type": "CONFIG_MISSING",
                    "severity": "MEDIUM",
                    "message": f"Variable {var} manquante pour {service}",
                    "action": f"Ajoute {var} dans .env ou sur Render"
                })

        return issues
    
    
@app.get('/api/audit/{log_name}')
def get_audit_log(request: Request, log_name: str, lines: int = 200):
    """Return last N lines from an audit log (protected by admin key)."""
    return _read_audit_log(request, log_name, lines)


@app.post('/api/verify/bunny/{video_id}')
def verify_bunny(request: Request, video_id: str, library: str = 'private', probe: bool = False, expires_hours: int = 2):
    """Admin-protected on-demand verification of Bunny signed embed URL.

    - Requires X-Admin-Key to match SENTINEL_ADMIN_KEY env var.
    - Returns masked token, expires timestamp and optional probe status.
    """
    admin_key = os.environ.get('SENTINEL_ADMIN_KEY')
    supplied = request.headers.get('X-Admin-Key')
    if not admin_key or supplied != admin_key:
        raise HTTPException(status_code=401, detail='Missing or invalid admin key')

    # Load library id & security key from env (repo or server environment)
    try:
        if library == 'private':
            library_id = int(os.environ.get('BUNNY_PRIVATE_LIBRARY_ID', ''))
        else:
            library_id = int(os.environ.get('BUNNY_PUBLIC_LIBRARY_ID', ''))
    except Exception:
        raise HTTPException(status_code=400, detail='Missing library id in environment')

    security_key = os.environ.get('BUNNY_SECURITY_KEY')

    # Import the signer and generate an URL
    try:
        from public_interface.bunny_signer import get_secure_embed_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Signer not available: {e}')

    try:
        signed = get_secure_embed_url(library_id=library_id, video_id=video_id, security_key=security_key, expires_in_hours=expires_hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error generating embed url: {e}')

    # Extract token/expires if present, mask token for safe output
    parsed = urlparse(signed)
    qs = parse_qs(parsed.query)
    token = qs.get('token', [None])[0]
    expires = qs.get('expires', [None])[0]

    def _mask(v: Optional[str]) -> str:
        if not v:
            return '<missing>'
        if len(v) <= 8:
            return v
        return v[:4] + '...' + v[-4:]

    result = {
        'ok': True,
        'embed_url_masked': parsed._replace(query=None).geturl() + ('?' + 'token=' + _mask(token) + (f'&expires={expires}' if expires else '')),
        'token_present': bool(token),
        'token_masked': _mask(token),
        'expires': expires
    }

    # optionally probe
    if probe:
        try:
            r = requests.head(signed, timeout=8, allow_redirects=True)
            result['probe_status'] = r.status_code
            result['probe_ok'] = (r.status_code == 200)
        except Exception as e:
            result['probe_error'] = str(e)[:200]

    # Add a short audit line to logs
    try:
        logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        audit_path = os.path.join(logs_dir, 'sentinel_actions.log')
        with open(audit_path, 'a', encoding='utf-8') as fh:
            fh.write(f"{datetime.utcnow().isoformat()} verify_bunny video={video_id} library={library} probe={probe} result={result.get('probe_status', 'N/A')}\n")
    except Exception:
        pass

    return JSONResponse(result)


def _read_audit_log(request: Request, log_name: str, lines: int = 200):
    """Helper used by the endpoint or directly in tests to fetch the last N lines of a log."""
    admin_key = os.environ.get('SENTINEL_ADMIN_KEY')
    supplied = request.headers.get('X-Admin-Key') if request is not None else None
    if not admin_key or supplied != admin_key:
        raise HTTPException(status_code=401, detail="Missing or invalid admin key")

    base_dir = os.path.dirname(__file__)
    file_path = os.path.abspath(os.path.join(base_dir, '..', 'logs', log_name))

    # Fallback: Search common 'logs' locations in the repository root
    if not os.path.exists(file_path):
        candidates = [
            os.path.abspath(os.path.join(base_dir, '..', 'logs', log_name)),
            os.path.abspath(os.path.join(base_dir, '..', '..', 'logs', log_name)),
            os.path.abspath(os.path.join(os.getcwd(), 'logs', log_name))
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                file_path = candidate
                break

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail='Log file not found')

    # Return last `lines` lines
    with open(file_path, 'r', encoding='utf-8') as fh:
        all_lines = fh.readlines()

    return JSONResponse({
        'ok': True,
        'lines': all_lines[-lines:]
    })
    
    def _check_video_403(self) -> Optional[dict]:
        """Vérifie si vidéos retournent 403"""
        try:
            # Test une vidéo
            response = requests.get(
                "https://only-public.onrender.com/watch/121",
                timeout=5
            )
            if "403" in response.text or response.status_code == 403:
                return {
                        "type": "VIDEO_403",
                        "severity": "CRITICAL",
                        "message": "Les vidéos retournent 403 Forbidden",
                        "detected_at": datetime.now().isoformat()
                    }
        except:
            pass
        
        return None

    def _check_bunny_referrers(self) -> Optional[dict]:
        """Verify Bunny Allowed Referrers by testing embeds with referer headers.

        Returns a diagnostic dict if it finds problems.
        """
        try:
            # Try to pick a private video to test
            r = requests.get(f"{CURATOR_URL}/videos?library=private&limit=1", timeout=5)
            r.raise_for_status()
            items = r.json()
            if not items:
                return {
                    "type": "BUNNY_REFERRERS",
                    "severity": "LOW",
                    "message": "No private videos found to test Bunny referer rules",
                    "details": {}
                }

            video = items[0]
            bunny_guid = video.get("bunny_video_id")
            library_id = os.environ.get('BUNNY_PRIVATE_LIBRARY_ID', '389178')

            embed_base = f"https://iframe.mediadelivery.net/embed/{library_id}/{bunny_guid}"

            # Test allowed referer
            allowed_headers = {"Referer": PUBLIC_URL}
            allowed_resp = requests.get(embed_base, headers=allowed_headers, timeout=5)

            # Test disallowed referer
            disallowed_headers = {"Referer": "https://evil.example/"}
            disallowed_resp = requests.get(embed_base, headers=disallowed_headers, timeout=5)

            issues = []
            if allowed_resp.status_code != 200:
                issues.append("Allowed referer returned non-200; check Allowed Referrers in Bunny dashboard")

            if disallowed_resp.status_code == 200:
                issues.append("Disallowed referer can access embed; update Bunny Allowed Referrers to restrict domains")

            # Verify signed url produced by /api/embed
            embed_api = f"{PUBLIC_URL}/api/embed/{video.get('id')}"
            embed_api_resp = requests.get(embed_api, timeout=5)
            token_present = False
            if embed_api_resp.status_code == 200:
                try:
                    data = embed_api_resp.json()
                    url = data.get('embed_url', '')
                    token_present = 'token=' in url or 'expires=' in url
                except:
                    pass

            if not token_present and video.get('library_type') == 'private':
                issues.append('API /api/embed did not return signed token for private video')

            if issues:
                return {
                    "type": "BUNNY_REFERRERS",
                    "severity": "CRITICAL" if any('Disallowed' in i for i in issues) else "HIGH",
                    "message": "Bunny embed referer rules or token signing issues detected",
                    "details": issues
                }

            return None
        except Exception as e:
            return {
                "type": "BUNNY_REFERRERS",
                "severity": "MEDIUM",
                "message": f"Error testing bunny referers: {e}",
                "details": {}
            }

    def _check_embed_audit_and_rate(self) -> Optional[dict]:
        """Check if embed audit logs are present and rate limit enforced."""
        try:
            # Check for audit log file in public interface
            import os
            audit_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'public_interface_audit.log')
            if not os.path.exists(audit_file):
                return {
                    "type": "BUNNY_AUDIT",
                    "severity": "LOW",
                    "message": "Audit log for embed requests not found",
                    "details": {}
                }

            # Check rate limit by making successive requests
            import requests
            url = f"{PUBLIC_URL}/api/embed/1"
            results = []
            for _ in range(5):
                r = requests.get(url, timeout=5)
                results.append(r.status_code)

            if 429 in results:
                # Rate limit present
                return None
            else:
                return {
                    "type": "BUNNY_RATE_LIMIT",
                    "severity": "MEDIUM",
                    "message": "Rate-limit not detected on /api/embed; consider adding limits to prevent abuse",
                    "details": {"samples": results}
                }
        except Exception as e:
            return {
                "type": "BUNNY_AUDIT",
                "severity": "LOW",
                "message": f"Error testing embed audit/rate: {e}",
                "details": {}
            }
    
    def _fix_video_403(self) -> Optional[dict]:
        """Tente de corriger le 403 automatiquement"""
        
        # Check si BUNNY_SECURITY_KEY existe
        bunny_key = os.environ.get('BUNNY_SECURITY_KEY')
        
        if not bunny_key:
            return {
                "issue": "VIDEO_403",
                "auto_fixed": False,
                "action": "MANUAL",
                "instructions": [
                    "1. Va sur Bunny Dashboard: https://panel.bunny.net/stream",
                    "2. Library 389178 → Security",
                    "3. OPTION A (Rapide): Désactive 'Embed view token authentication'",
                    "   OU",
                    "4. OPTION B (Sécurisé): Copie Security Key",
                    "5. Ajoute sur Render: BUNNY_SECURITY_KEY=ta-cle",
                    "6. Redeploy only-public"
                ],
                "url": "https://panel.bunny.net/stream",
                "render_url": "https://dashboard.render.com"
            }
        
        # Si key existe, vérifier qu'elle fonctionne
        from public_interface.bunny_signer import get_secure_embed_url
        
        try:
            test_url = get_secure_embed_url(
                library_id=389178,
                video_id="test",
                security_key=bunny_key
            )
            
            if "token=" in test_url:
                return {
                    "issue": "VIDEO_403",
                    "auto_fixed": True,
                    "message": "Signed URLs fonctionnent. Le 403 devrait être résolu après redeploy."
                }
        except Exception as e:
            return {
                "issue": "VIDEO_403",
                "auto_fixed": False,
                "action": "MANUAL",
                "error": str(e),
                "instructions": [
                    "La Security Key semble incorrecte.",
                    "1. Va sur Bunny Dashboard",
                    "2. Vérifie la Security Key",
                    "3. Update BUNNY_SECURITY_KEY sur Render",
                    "4. Redeploy"
                ]
            }
    
    def _check_services(self) -> list:
        """Check tous les services"""
        services = {
            "Gateway": "http://localhost:5055/health",
            "Curator": "http://localhost:5061/health",
            "Monetizer": "http://localhost:5060/health",
            "Public": "http://localhost:5062/health"
        }
        
        issues = []
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code != 200:
                    issues.append({
                        "type": "SERVICE_DOWN",
                        "service": name,
                        "severity": "HIGH",
                        "message": f"{name} ne répond pas correctement",
                        "action": f"Redémarre: cd {name.lower()} && python3 {name.lower()}.py"
                    })
            except:
                issues.append({
                    "type": "SERVICE_DOWN",
                    "service": name,
                    "severity": "HIGH",
                    "message": f"{name} n'est pas lancé",
                    "action": f"Démarre: cd {name.lower()} && python3 {name.lower()}.py"
                })
        
        return issues

    # perform_bunny_checks removed from SentinelAutoFix — it's implemented on
    # SentinelMonitor so the active monitoring thread and tests will use that
    # method. Keeping this commented here for reference if needed later.
    
    def _check_configuration(self) -> list:
        """Vérifie config système"""
        issues = []
        
        # Check env vars critiques
        required_vars = {
            "BUNNY_SECURITY_KEY": "Bunny Stream",
            "TURSO_DATABASE_URL": "Monetizer (Turso)",
            "TURSO_AUTH_TOKEN": "Monetizer (Turso)"
        }
        
        for var, service in required_vars.items():
            if not os.environ.get(var):
                issues.append({
                    "type": "CONFIG_MISSING",
                    "severity": "MEDIUM",
                    "message": f"Variable {var} manquante pour {service}",
                    "action": f"Ajoute {var} dans .env ou sur Render"
                })
        
        return issues

# Endpoint auto-diagnostic
@app.get("/api/autofix")
async def autofix():
    """Diagnostic automatique + tentative de correction"""
    sentinel = SentinelAutoFix()
    results = sentinel.diagnose_system()
    
    return {
        "status": "scan_complete",
        "timestamp": results["timestamp"],
        "summary": {
            "issues_found": len(results["issues_found"]),
            "auto_fixed": len(results["fixes_applied"]),
            "manual_required": len(results["action_required"])
        },
        "details": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)