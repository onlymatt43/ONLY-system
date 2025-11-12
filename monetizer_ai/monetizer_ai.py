import os, re, hmac, base64, json, sqlite3, secrets, io, csv
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse, HTMLResponse, RedirectResponse
from dotenv import load_dotenv
from slugify import slugify
import qrcode
from dateutil import parser as dtparse

load_dotenv()

PORT            = int(os.getenv("PORT","5060"))
DB_PATH         = os.getenv("DB_PATH","./monetizer.db")
# Créer le dossier parent si nécessaire (pour Render sans Disk)
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
BASE_URL        = os.getenv("BASE_URL","http://localhost:5060").rstrip("/")
SECRET_KEY      = os.getenv("SECRET_KEY","change-me-super-long-secret")
CODE_PREFIX     = os.getenv("CODE_PREFIX","OM43")
DEFAULT_DURATION= int(os.getenv("DEFAULT_DURATION_MIN","1440"))

app = FastAPI(title="Monetizer AI", version="1.0")

# ───────────────────────────────── DB
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS tokens(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code_visible TEXT UNIQUE,
          token TEXT UNIQUE,          -- compact signed token
          token_hash TEXT,            -- HMAC digest base64
          title TEXT,
          value_cents INTEGER,
          duration_min INTEGER,
          vendor_url TEXT,
          unlock_url TEXT,            -- URL d'unlock (vers WP)
          status TEXT,                -- fresh | activated | expired | revoked
          created_at TEXT,
          activated_at TEXT,
          expires_at TEXT,
          meta TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tokens_status ON tokens(status)")
    print("[DB] ready:", DB_PATH)

def now_utc():
    return datetime.now(timezone.utc)

def fmt(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None

# ──────────────────────────────── Crypto helpers
def sign(payload: str) -> str:
    mac = hmac.new(SECRET_KEY.encode(), payload.encode(), sha256).digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")

def make_token(code_visible: str, minutes: int) -> Dict[str,str]:
    """Compact token = base64url(code|exp_ts|sig)"""
    exp_ts = int((now_utc() + timedelta(minutes=minutes)).timestamp())
    msg = f"{code_visible}|{exp_ts}"
    sig = sign(msg)
    raw = f"{code_visible}|{exp_ts}|{sig}"
    tok = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    return {"token": tok, "exp_ts": exp_ts, "sig": sig}

def parse_token(token: str) -> Optional[Dict[str,Any]]:
    try:
        pad = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(token + pad).decode()
        code, exp_ts, sig = raw.split("|")
        exp_ts = int(exp_ts)
        if sign(f"{code}|{exp_ts}") != sig:
            return None
        return {"code": code, "exp_ts": exp_ts, "sig": sig}
    except Exception:
        return None

# ──────────────────────────────── Utilities
ALNUM = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans I/O/1/0
def rand_code(n=4):
    return "".join(secrets.choice(ALNUM) for _ in range(n))

def pretty_code(prefix: str) -> str:
    return f"{prefix}-{rand_code()}-{rand_code()}"

def ensure_url(u: Optional[str]) -> Optional[str]:
    if not u: return None
    return u.strip() or None

def build_unlock_url(token: str) -> str:
    # URL que tu mettras dans WP (bouton "Unlock" ou QR). 
    # Peut pointer vers une page d'intermédiation jolie /u/{token} -> redirige vers /verify
    return f"{BASE_URL}/u/{token}"

# ──────────────────────────────── Core ops
def mint_one(title:str, value_cents:int, duration_min:int, vendor_url:Optional[str], meta:dict) -> Dict[str,Any]:
    code = pretty_code(CODE_PREFIX)
    tk = make_token(code, duration_min)
    token = tk["token"]
    token_hash = sign(token)  # double signature (anti-leak rapide)
    unlock_url = build_unlock_url(token)
    with db() as c:
        c.execute("""INSERT INTO tokens(code_visible, token, token_hash, title, value_cents, duration_min,
                     vendor_url, unlock_url, status, created_at, meta)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (code, token, token_hash, title, value_cents, duration_min,
                   vendor_url, unlock_url, "fresh", fmt(now_utc()), json.dumps(meta or {}, ensure_ascii=False)))
        tid = c.lastrowid
        row = c.execute("SELECT * FROM tokens WHERE id = ?", (tid,)).fetchone()
        return dict(row)

def set_status(tid:int, status:str, expires_at:Optional[datetime]=None):
    with db() as c:
        c.execute("UPDATE tokens SET status=?, expires_at=?, activated_at=COALESCE(activated_at, ?) WHERE id=?",
                  (status, fmt(expires_at), fmt(now_utc()), tid))

def activate_or_refresh(row: sqlite3.Row) -> Dict[str,Any]:
    """Active un token fresh → activated; si activated, vérifie expiry; si expired/revoked -> KO."""
    status = row["status"]
    if status in ("revoked","expired"):
        return {"ok":False, "reason": status}
    # Vérifie expiry par signature (exp_ts dans le token)
    p = parse_token(row["token"])
    if not p: 
        return {"ok":False, "reason":"bad_signature"}
    exp_dt = datetime.fromtimestamp(p["exp_ts"], tz=timezone.utc)
    if exp_dt < now_utc():
        # expire en DB
        with db() as c:
            c.execute("UPDATE tokens SET status=?, expires_at=? WHERE id=?",
                      ("expired", fmt(exp_dt), row["id"]))
        return {"ok":False, "reason":"expired", "expires_at": fmt(exp_dt)}
    # Passe en activated si fresh
    if status == "fresh":
        with db() as c:
            c.execute("UPDATE tokens SET status=?, activated_at=?, expires_at=? WHERE id=?",
                      ("activated", fmt(now_utc()), fmt(exp_dt), row["id"]))
    return {"ok":True, "expires_at": fmt(exp_dt)}

# ──────────────────────────────── QR helper
def qr_png(data:str) -> bytes:
    img = qrcode.make(data)  # PIL image
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ──────────────────────────────── API
@app.on_event("startup")
def _boot():
    init_db()

@app.get("/")
def root():
    return {"status":"Monetizer online", "base": BASE_URL}

# Mint simple (unitaire)
@app.post("/mint")
async def mint(req: Request):
    """
    JSON attendu:
    {
      "title": "ONLY ACCESS — Episode 01",
      "value_cents": 1000,          # optionnel
      "duration_min": 1440,
      "vendor_url": "https://payhip.com/..",    # optionnel
      "meta": {"series":"ONLYGOLD","note":"drop 01"}
    }
    """
    j = await req.json()
    title = j.get("title") or "OM43 Access"
    value_cents = int(j.get("value_cents") or 0)
    duration_min = int(j.get("duration_min") or DEFAULT_DURATION)
    vendor_url = ensure_url(j.get("vendor_url"))
    meta = j.get("meta") or {}
    row = mint_one(title, value_cents, duration_min, vendor_url, meta)
    return {
        "ok": True,
        "id": row["id"],
        "code": row["code_visible"],
        "token": row["token"],
        "unlock_url": row["unlock_url"],
        "duration_min": row["duration_min"],
        "status": row["status"]
    }

# Mint batch (idéal pour cartes cadeaux)
@app.post("/mint/batch")
async def mint_batch(req: Request):
    """
    JSON:
    {
      "count": 25,
      "title": "ONLY ACCESS GIFT",
      "value_cents": 1500,
      "duration_min": 1440,
      "vendor_url": "https://...",  # facultatif
      "meta": {"campaign":"black-friday"}
    }
    """
    j = await req.json()
    n = max(1, min(500, int(j.get("count", 10))))
    title = j.get("title") or "OM43 Access"
    value_cents = int(j.get("value_cents") or 0)
    duration_min = int(j.get("duration_min") or DEFAULT_DURATION)
    vendor_url = ensure_url(j.get("vendor_url"))
    meta = j.get("meta") or {}
    out = []
    for _ in range(n):
        row = mint_one(title, value_cents, duration_min, vendor_url, meta)
        out.append({"id": row["id"], "code": row["code_visible"], "token": row["token"], "unlock_url": row["unlock_url"]})
    return {"ok":True, "count": len(out), "items": out}

# Export CSV (id, code, token, unlock_url, vendor_url, expiry)
@app.get("/export/csv")
def export_csv():
    with db() as c:
        rows = c.execute("SELECT id,code_visible,token,vendor_url,unlock_url,duration_min,status,created_at,expires_at FROM tokens ORDER BY id DESC").fetchall()
    def gen():
        w = io.StringIO()
        cw = csv.writer(w)
        cw.writerow(["id","code_visible","token","vendor_url","unlock_url","duration_min","status","created_at","expires_at"])
        yield w.getvalue(); w.seek(0); w.truncate(0)
        for r in rows:
            cw.writerow([r["id"], r["code_visible"], r["token"], r["vendor_url"], r["unlock_url"], r["duration_min"], r["status"], r["created_at"], r["expires_at"]])
            yield w.getvalue(); w.seek(0); w.truncate(0)
    headers = {"Content-Disposition": 'attachment; filename="tokens_export.csv"'}
    return StreamingResponse(gen(), media_type="text/csv", headers=headers)

# QR direct (PNG)
@app.get("/qr/{token}")
def qr(token: str):
    png = qr_png(f"{BASE_URL}/u/{token}")
    return Response(content=png, media_type="image/png")

# Landing courte (jolie) pour les QR: redirige vers /verify
@app.get("/u/{token}")
def unlock_redirect(token: str):
    return RedirectResponse(url=f"{BASE_URL}/verify?token={token}")

# Vérification (à appeler depuis ton plugin WP)
@app.get("/verify")
def verify(token: str):
    parsed = parse_token(token)
    if not parsed:
        return JSONResponse({"ok":False, "reason":"invalid_token"}, status_code=400)
    with db() as c:
        row = c.execute("SELECT * FROM tokens WHERE token = ?", (token,)).fetchone()
    if not row:
        return JSONResponse({"ok":False, "reason":"unknown"}, status_code=404)

    res = activate_or_refresh(row)
    if not res["ok"]:
        return {"ok":False, "reason":res["reason"], "expires_at":res.get("expires_at")}
    # cookie_hint : seconds restants → utile pour WP (durée du cookie)
    expires_at = dtparse.parse(res["expires_at"])
    remaining = int((expires_at - now_utc()).total_seconds())
    return {
        "ok": True,
        "code": row["code_visible"],
        "title": row["title"],
        "expires_at": res["expires_at"],
        "remaining_sec": max(0, remaining),
        "cookie_hint_sec": max(60, remaining),  # tu peux plafonner côté WP
        "status": "activated"
    }

# Révocation manuelle (ex.: remboursement, fraude)
@app.post("/revoke")
async def revoke(req: Request):
    j = await req.json()
    token = j.get("token")
    if not token: return {"ok":False, "error":"missing token"}
    with db() as c:
        r = c.execute("SELECT * FROM tokens WHERE token=?", (token,)).fetchone()
        if not r: return {"ok":False, "error":"unknown"}
        c.execute("UPDATE tokens SET status=? WHERE token=?", ("revoked", token))
    return {"ok":True, "status":"revoked"}

# Mini liste (debug)
@app.get("/tokens")
def list_tokens(limit:int=50):
    with db() as c:
        rows = c.execute("SELECT id,code_visible,token,status,expires_at,unlock_url FROM tokens ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

# Page HTML ultra simple (optionnel)
@app.get("/info/{code}", response_class=HTMLResponse)
def info_page(code:str):
    with db() as c:
        r = c.execute("SELECT * FROM tokens WHERE code_visible=?", (code,)).fetchone()
    if not r:
        return HTMLResponse("<h1>Code inconnu</h1>", status_code=404)
    return HTMLResponse(f"""
    <html><body style="font-family:system-ui;background:#111;color:#fff">
      <h1>ONLY ACCESS</h1>
      <p><b>Code:</b> {r['code_visible']}</p>
      <p><b>Status:</b> {r['status']}</p>
      <p><b>Unlock URL:</b> <a href="{r['unlock_url']}" style="color:#fff">{r['unlock_url']}</a></p>
      <img src="{BASE_URL}/qr/{r['token']}" alt="QR" style="max-width:240px;margin-top:10px"/>
    </body></html>
    """)
    
if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
