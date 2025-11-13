import os
import time
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import requests

load_dotenv()

PORT = int(os.getenv("PORT", "5059"))
REFRESH_SEC = int(os.getenv("REFRESH_SEC", "5"))

CURATOR_URL = os.getenv("CURATOR_URL", "")
NARRATOR_URL = os.getenv("NARRATOR_URL", "http://localhost:5056/")
BUILDER_URL = os.getenv("BUILDER_URL", "http://localhost:5057/")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5055/")
PUBLISHER_URL = os.getenv("PUBLISHER_URL", "http://localhost:5058/")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

app = FastAPI(title="Sentinel Dashboard", version="1.0")


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


@app.get("/api/jobs")
def api_jobs(limit: int = 100):
    return JSONResponse(fetch_jobs(limit=limit))


@app.get("/api/services")
def api_services():
    return JSONResponse(service_status_map())


@app.get("/health")
def health():
    return {"ok": True, "ts": int(time.time())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
