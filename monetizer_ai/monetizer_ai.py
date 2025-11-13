import os, re, hmac, base64, json, secrets
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

PORT            = int(os.getenv("PORT","5060"))
TURSO_URL       = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN     = os.getenv("TURSO_AUTH_TOKEN")
SECRET_KEY      = os.getenv("SECRET_KEY","change-me-super-long-secret")
CODE_PREFIX     = os.getenv("CODE_PREFIX","OM43")

# Import Turso client
from libsql_client import create_client_sync

app = FastAPI(title="Monetizer AI (Turso)", version="2.0")

# ───────────────────────────────── DB
_client = None

def db():
    """Return Turso client"""
    global _client
    if not _client:
        # Force HTTP mode instead of WebSocket
        url = TURSO_URL.replace("libsql://", "https://")
        _client = create_client_sync(url=url, auth_token=TURSO_TOKEN)
    return _client

def init_db():
    client = db()
    client.execute("""
    CREATE TABLE IF NOT EXISTS tokens(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      code TEXT UNIQUE,
      token TEXT UNIQUE,
      access_level TEXT,
      video_id INTEGER,
      expires_at TEXT,
      created_at TEXT
    )""")
    print("[DB] Turso table 'tokens' ready")

# ───────────────────────────────── TOKEN UTILS
def sign_token(data: str) -> str:
    """HMAC-SHA256 signature"""
    return base64.urlsafe_b64encode(
        hmac.new(SECRET_KEY.encode(), data.encode(), sha256).digest()
    ).decode().rstrip("=")

def parse_token(token: str) -> Optional[Dict[str, Any]]:
    """Parse and verify token format: BASE64(code|timestamp|signature)"""
    try:
        decoded = base64.urlsafe_b64decode(token + "==")
        parts = decoded.decode().split("|")
        if len(parts) != 3:
            return None
        code, exp_ts, sig = parts
        # Verify signature
        expected_sig = sign_token(f"{code}|{exp_ts}")
        if not hmac.compare_digest(sig, expected_sig):
            return None
        return {"code": code, "exp_ts": int(exp_ts), "sig": sig}
    except Exception:
        return None

def pretty_code(prefix: str = CODE_PREFIX) -> str:
    """Generate readable code like OM43-ABCD-1234"""
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    return f"{prefix}-{part1}-{part2}"

def make_long_token(code: str, exp_ts: int) -> str:
    """Create long base64 token from code"""
    sig = sign_token(f"{code}|{exp_ts}")
    payload = f"{code}|{exp_ts}|{sig}"
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

# ───────────────────────────────── ENDPOINTS
@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def index():
    return {"status": "Monetizer AI (Turso)", "version": "2.0"}

@app.post("/mint")
def mint(req: Dict[str, Any]):
    """
    Create new token
    {
      "title": "VIP Access",
      "access_level": "vip|public|ppv",
      "video_id": null or int,
      "duration_days": 365
    }
    """
    title = req.get("title", "Access Token")
    access_level = req.get("access_level", "public")
    video_id = req.get("video_id")
    duration_days = int(req.get("duration_days", 365))
    
    code = pretty_code()
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(days=duration_days)
    exp_ts = int(expires_at.timestamp())
    
    token = make_long_token(code, exp_ts)
    
    client = db()
    result = client.execute(
        "INSERT INTO tokens(code, token, access_level, video_id, expires_at, created_at) VALUES(?,?,?,?,?,?)",
        [code, token, access_level, video_id, expires_at.isoformat(), created_at.isoformat()]
    )
    
    return {
        "ok": True,
        "id": result.last_insert_rowid,
        "code": code,
        "token": token,
        "access_level": access_level,
        "video_id": video_id,
        "expires_at": expires_at.isoformat(),
        "created_at": created_at.isoformat()
    }

@app.get("/verify")
def verify(token: str):
    """
    Verify token (short code OR long token)
    Returns: {"ok": true/false, "access_level": "...", "video_id": ..., "expires_at": "..."}
    """
    client = db()
    parsed = parse_token(token)
    
    if parsed:
        # Long token - search by token field
        result = client.execute("SELECT * FROM tokens WHERE token = ?", [token])
    else:
        # Short code - search by code field
        result = client.execute("SELECT * FROM tokens WHERE code = ?", [token])
    
    rows = result.rows
    if not rows:
        return JSONResponse({"ok": False, "reason": "unknown"}, status_code=404)
    
    row = rows[0]
    # row is a tuple, columns are: id, code, token, access_level, video_id, expires_at, created_at
    row_dict = {
        "id": row[0],
        "code": row[1],
        "token": row[2],
        "access_level": row[3],
        "video_id": row[4],
        "expires_at": row[5],
        "created_at": row[6]
    }
    
    # Check expiration
    expires_at = datetime.fromisoformat(row_dict["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        return JSONResponse({"ok": False, "reason": "expired"}, status_code=403)
    
    return {
        "ok": True,
        "access_level": row_dict["access_level"],
        "video_id": row_dict["video_id"],
        "expires_at": row_dict["expires_at"],
        "code": row_dict["code"]
    }

@app.post("/revoke")
def revoke(req: Dict[str, Any]):
    """Revoke/delete a token by code or token"""
    token = req.get("token") or req.get("code")
    if not token:
        return {"ok": False, "error": "missing token or code"}
    
    client = db()
    result = client.execute("DELETE FROM tokens WHERE code = ? OR token = ?", [token, token])
    
    return {"ok": True, "deleted": result.rows_affected > 0}

@app.get("/tokens")
def list_tokens(limit: int = 100):
    """List all tokens"""
    client = db()
    result = client.execute("SELECT * FROM tokens ORDER BY id DESC LIMIT ?", [limit])
    
    tokens = []
    for row in result.rows:
        tokens.append({
            "id": row[0],
            "code": row[1],
            "token": row[2],
            "access_level": row[3],
            "video_id": row[4],
            "expires_at": row[5],
            "created_at": row[6]
        })
    
    return {"ok": True, "tokens": tokens}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
