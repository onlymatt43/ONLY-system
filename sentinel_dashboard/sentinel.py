import os
import time
import threading
from typing import List, Dict, Any
from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import requests

# Import Sentinel AI
from sentinel_ai import SentinelAI

load_dotenv()

PORT = int(os.getenv("PORT", "5059"))
REFRESH_SEC = int(os.getenv("REFRESH_SEC", "5"))
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL_SEC", "30"))  # AI monitoring cycle

CURATOR_URL = os.getenv("CURATOR_URL", "")
NARRATOR_URL = os.getenv("NARRATOR_URL", "http://localhost:5056/")
BUILDER_URL = os.getenv("BUILDER_URL", "http://localhost:5057/")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5055/")
PUBLISHER_URL = os.getenv("PUBLISHER_URL", "http://localhost:5058/")
MONETIZER_URL = os.getenv("MONETIZER_URL", "http://localhost:5060/")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5062/")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

app = FastAPI(title="Sentinel AI Dashboard", version="2.0")

# Initialize Sentinel AI
SERVICES_CONFIG = {
    "Gateway": GATEWAY_URL,
    "Narrator": NARRATOR_URL,
    "Builder": BUILDER_URL,
    "Publisher": PUBLISHER_URL,
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
    return {
        "Curator": ping(CURATOR_URL),
        "Narrator": ping(NARRATOR_URL),
        "Builder": ping(BUILDER_URL),
        "Gateway": ping(GATEWAY_URL),
        "Publisher": ping(PUBLISHER_URL),
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
