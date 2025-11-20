import os
import json
import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import requests
from tenacity import retry, wait_fixed, stop_after_attempt

load_dotenv()

PORT = int(os.getenv("PORT", "5055"))
NARRATOR_URL = os.getenv("NARRATOR_URL", "http://localhost:5056/describe")
BUILDER_URL = os.getenv("BUILDER_URL", "http://localhost:5057/build")
PUBLISHER_URL = os.getenv("PUBLISHER_URL", "http://localhost:5058/notify")
WORKER_INTERVAL = int(os.getenv("WORKER_INTERVAL_SEC", "2"))

DB_PATH = os.getenv("DB_PATH", "./gateway.db")
# Créer le dossier parent si nécessaire (pour Render sans Disk)
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)

app = FastAPI(title="OM43 Gateway", version="1.0")


# ---------------- DB utils ----------------
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS jobs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                narrator_json TEXT,
                post_id INTEGER,
                link TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_file ON jobs(file)")
    print(f"[DB] ready: {DB_PATH}")


def now():
    return datetime.utcnow().isoformat(timespec="seconds")


def get_job_by_file(path: str) -> Optional[sqlite3.Row]:
    with db() as c:
        row = c.execute(
            "SELECT * FROM jobs WHERE file = ? ORDER BY id DESC LIMIT 1",
            (path,)
        ).fetchone()
        return row


def insert_job(path: str) -> int:
    with db() as c:
        ts = now()
        c.execute(
            "INSERT INTO jobs(file, status, created_at, updated_at) VALUES(?,?,?,?)",
            (path, "queued", ts, ts)
        )
        return c.lastrowid


def set_status(job_id: int, status: str, **kwargs):
    fields = ["status = ?", "updated_at = ?"]
    values = [status, now()]
    
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
    
    values.append(job_id)
    
    with db() as c:
        c.execute(
            f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?",
            values
        )


def next_queued() -> Optional[sqlite3.Row]:
    with db() as c:
        row = c.execute(
            "SELECT * FROM jobs WHERE status = 'queued' ORDER BY id ASC LIMIT 1"
        ).fetchone()
        return row


# --------------- HTTP helpers ---------------
@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def call_narrator(file_path: str) -> Dict[str, Any]:
    r = requests.post(NARRATOR_URL, json={"file": file_path}, timeout=60)
    r.raise_for_status()
    return r.json()


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def call_builder(meta: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(BUILDER_URL, json=meta, timeout=120)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Builder error {r.status_code}: {r.text[:400]}")
    return r.json()


def notify_publisher(title: str, link: str):
    """Notifie le Publisher AI (emails + réseaux)"""
    try:
        # Notification simple
        requests.post(
            PUBLISHER_URL,
            json={"title": title, "link": link},
            timeout=10
        )
        
        # Publication sociale (optionnel)
        requests.post(
            f"{PUBLISHER_URL.replace('/notify', '/social/publish')}",
            json={
                "title": title,
                "link": link,
                "description": ""
            },
            timeout=300
        )
    except Exception as e:
        print(f"[Gateway] ⚠️ Publisher skip: {e}")


# --------------- Worker loop ---------------
def worker():
    print("[Worker] started")
    
    while True:
        try:
            job = next_queued()
            if not job:
                time.sleep(WORKER_INTERVAL)
                continue
            
            job_id = job["id"]
            file_path = job["file"]
            
            print(f"[Worker] processing job #{job_id} → {file_path}")
            set_status(job_id, "running")
            
            # 1) Narrator
            meta = call_narrator(file_path)
            safe_meta = json.dumps(meta, ensure_ascii=False)
            set_status(job_id, "running", narrator_json=safe_meta)
            
            # 2) Builder
            build_result = call_builder(meta)
            post_id = build_result.get("post_id")
            link = build_result.get("link")
            
            set_status(job_id, "done", post_id=post_id, link=link, last_error=None)
            
            print(f"[Worker] ✅ job #{job_id} DONE → post_id={post_id} | {link}")
            
            # 3) Notify Publisher
            notify_publisher(meta.get("title", "New content"), link or "")
            
        except Exception as e:
            msg = str(e)[:800]
            try:
                set_status(job_id, "error", last_error=msg)
            except Exception:
                pass
            print(f"[Worker] ⚠️ error: {msg}")
        
        time.sleep(WORKER_INTERVAL)


# --------------- API ----------------
@app.on_event("startup")
def _boot():
    init_db()
    threading.Thread(target=worker, daemon=True).start()


@app.get("/")
def index():
    return {
        "status": "gateway online",
        "narrator": NARRATOR_URL,
        "builder": BUILDER_URL,
        "publisher": PUBLISHER_URL
    }


@app.post("/event")
async def create_event(request: Request):
    """Create new job from event"""
    try:
        data = await request.json()
        
        # ✅ FIX: Log payload reçu pour debug
        print(f"📦 Received payload: {data}")
        
        # ✅ FIX: Validation flexible des champs
        event_type = data.get("event")
        file_path = data.get("file")
        
        if not event_type or not file_path:
            print(f"❌ Missing fields. event={event_type}, file={file_path}")
            return {
                "ok": False,
                "error": "Missing required fields: 'event' and 'file' are required"
            }
        
        # Champs optionnels
        title = data.get("title", "Untitled")
        timestamp = data.get("timestamp")
        
        # Créer job ID unique
        import uuid
        job_id = str(uuid.uuid4())
        
        # Insérer dans DB
        import time
        db_conn = db()
        db_conn.execute("""
            INSERT INTO jobs (id, file, title, status, timestamp, created_at)
            VALUES (?, ?, ?, 'queued', ?, ?)
        """, (job_id, file_path, title, timestamp or time.time(), time.time()))
        db_conn.commit()
        
        print(f"✅ Job created: {job_id}")
        
        return {
            "ok": True,
            "job_id": job_id,
            "message": f"Job queued: {title}"
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return {"ok": False, "error": "Invalid JSON payload"}
    except Exception as e:
        print(f"❌ Error creating job: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}


@app.get("/jobs")
def list_jobs(limit: int = 50):
    with db() as c:
        rows = c.execute(
            "SELECT * FROM jobs ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    with db() as c:
        r = c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not r:
            return {"error": "not found"}
        return dict(r)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gateway",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
