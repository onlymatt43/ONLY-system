import os
import time
import threading
from typing import List, Dict, Any
from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import requests
from datetime import datetime

# Import Sentinel AI
from sentinel_ai import SentinelAI

load_dotenv()

# ✅ FIX: Port cohérent
PORT = int(os.environ.get("PORT", 5059))  # 5059 en local, 10000 sur Render

REFRESH_SEC = int(os.getenv("REFRESH_SEC", "5"))
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL_SEC", "30"))  # AI monitoring cycle

CURATOR_URL = os.getenv("CURATOR_URL", "https://only-curator.onrender.com/")
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://only-gateway.onrender.com/")
MONETIZER_URL = os.getenv("MONETIZER_URL", "https://only-monetizer.onrender.com/")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://only-public.onrender.com/")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

app = FastAPI(title="Sentinel AI Dashboard", version="2.0")

# Initialize Sentinel AI - ONLY Core Services (WordPress pipeline removed)
SERVICES_CONFIG = {
    "Gateway": GATEWAY_URL,
    "Curator": CURATOR_URL,
    "Monetizer": MONETIZER_URL,
    "Public": PUBLIC_URL
}

sentinel_ai = SentinelAI(SERVICES_CONFIG)

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
    
    def start_monitoring(self):
        """Start continuous health checks"""
        self.is_active = True
        print("🛡️ Sentinel activated - Monitoring system")
        
        def monitor_loop():
            while self.is_active:
                self.perform_health_check()
                time.sleep(30)  # Check every 30 seconds
        
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
            if fix["auto_fixed"]:
                results["fixes_applied"].append(fix)
            else:
                results["action_required"].append(fix)
        
        # 2. Check services down
        services_down = self._check_services()
        results["issues_found"].extend(services_down)
        
        # 3. Check config errors
        config_errors = self._check_configuration()
        results["issues_found"].extend(config_errors)
        
        return results
    
    def _check_video_403(self) -> dict:
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
    
    def _fix_video_403(self) -> dict:
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)