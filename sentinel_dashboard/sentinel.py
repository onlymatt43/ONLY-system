import os
import sqlite3
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import urllib.parse
import requests

load_dotenv()

PORT = int(os.getenv("PORT", "5059"))
GATEWAY_DB = os.getenv("GATEWAY_DB", "../gateway/gateway.db")
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
def db_conn() -> Optional[sqlite3.Connection]:
    if not os.path.exists(GATEWAY_DB):
        return None
    # lecture seule via URI
    uri = f"file:{urllib.parse.quote(GATEWAY_DB)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = db_conn()
    if not conn:
        return []
    with conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


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
    has_db = os.path.exists(GATEWAY_DB)
    
    html = tmpl.render(
        refresh=REFRESH_SEC,
        has_db=has_db,
        db_path=os.path.abspath(GATEWAY_DB),
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
