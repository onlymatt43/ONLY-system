#!/usr/bin/env python3
"""
PUBLIC INTERFACE - ONLY System
Interface publique client Netflix-style pour viewers/subscribers
Port: 5062
"""

import os
import requests
from fastapi import FastAPI, Request, HTTPException, Cookie
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.extension import Limiter as LimiterExt
except Exception:
    Limiter = None
    get_remote_address = None
    RateLimitExceeded = None
    SlowAPIMiddleware = None
    LimiterExt = None
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from public_interface.bunny_signer import get_secure_embed_url
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import logging
import uvicorn
from dotenv import load_dotenv
import hmac
import hashlib
import time

# Configuration
PORT = int(os.getenv("PORT", "5062"))

# ✅ Charge .env depuis racine projet ET dossier courant
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Environment detection
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')
IS_PRODUCTION = ENVIRONMENT == 'production'

# Service URLs
CURATOR_URL = os.environ.get('CURATOR_URL', 'http://localhost:5061')
MONETIZER_URL = os.environ.get('MONETIZER_URL', 'http://localhost:5060')
GATEWAY_URL = os.environ.get('GATEWAY_URL', 'http://localhost:5055')

BUNNY_SECURITY_KEY = os.environ.get('BUNNY_SECURITY_KEY')
BUNNY_PRIVATE_LIBRARY_ID = os.environ.get('BUNNY_PRIVATE_LIBRARY_ID', '389178')
BUNNY_PUBLIC_LIBRARY_ID = os.environ.get('BUNNY_PUBLIC_LIBRARY_ID', '420867')

if not BUNNY_SECURITY_KEY:
    print("⚠️ BUNNY_SECURITY_KEY non configurée")

app = FastAPI(title="ONLY - Public Interface", version="1.0.0")

# Rate limiting (slowapi) - limits per IP
# We always create an audit logger so sentinel and tests can find logs
logger = logging.getLogger("public_interface.audit")
logger.setLevel(logging.INFO)
os.makedirs("logs", exist_ok=True)
# Rotate daily, keep 7 days
from logging.handlers import TimedRotatingFileHandler
log_handler = TimedRotatingFileHandler("logs/public_interface_audit.log", when="D", interval=1, backupCount=7)
log_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
if not logger.handlers:
    logger.addHandler(log_handler)

try:
    # If a Redis storage URL is provided, use it for distributed limiting
    storage_url = os.environ.get("SLOWAPI_REDIS_URL")
    if storage_url:
        limiter = Limiter(key_func=get_remote_address, storage_uri=storage_url)
    else:
        limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    if SlowAPIMiddleware:
        app.add_middleware(SlowAPIMiddleware)

    # If slowapi is available, attach limiter middleware
except Exception:
    # slowapi may not be available in some environments; fallback to no limiter
    limiter = None
    print("⚠️ slowapi not available — rate limiting disabled")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add common security headers for all responses"""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    # Content-Security-Policy: allow iframes from Bunny embed CDN, and limit who can embed this site
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "frame-src https://iframe.mediadelivery.net 'self'; "
        "frame-ancestors 'self' https://only-public.onrender.com"
    )
    return response

# Static files & templates
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Ensure static dir exists (helps detect misconfigured working directories)
if not os.path.isdir(STATIC_DIR):
    print(f"FAIL Directory '{os.path.basename(STATIC_DIR)}' does not exist")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_session_token(video_id: str, access_token: Optional[str] = None) -> str:
    """Generate temporary session token for video access"""
    timestamp = int(time.time())
    data = f"{video_id}:{timestamp}:{access_token or 'anon'}"
    
    secret = os.environ.get('SECRET_KEY', 'change-me-in-production')
    signature = hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    return f"{signature}-{timestamp}"

def validate_session_token(token: str, video_id: str, max_age_seconds: int = 7200) -> bool:
    """Validate session token (2h expiry by default)"""
    try:
        signature, timestamp = token.rsplit('-', 1)
        timestamp = int(timestamp)
        
        if time.time() - timestamp > max_age_seconds:
            return False
        
        return len(signature) == 16
        
    except (ValueError, AttributeError):
        return False

def fetch_videos(category_id=None, tag_id=None, limit=50):
    """Fetch videos from Curator Bot"""
    try:
        params = {"limit": limit}
        if category_id:
            params["category_id"] = category_id
        if tag_id:
            params["tag_id"] = tag_id
        
        response = requests.get(f"{CURATOR_URL}/videos", params=params, timeout=5)
        response.raise_for_status()
        results = response.json()
        # Normalize for templates: ensure each video has a 'video_id' alias
        for v in results:
            if 'video_id' not in v and 'bunny_video_id' in v:
                v['video_id'] = v.get('bunny_video_id')
        return results
    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []

def verify_token(token: str):
    """Verify access token with Monetizer AI"""
    try:
        response = requests.get(
            f"{MONETIZER_URL}/verify",
            params={"token": token},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None

def check_video_access(video, token_data):
    """Check if user has access to video based on access_level"""
    if video.get("access_level") == "public":
        return True
    
    if not token_data:
        return False
    
    if token_data.get("access_level") == "vip":
        return True
    
    if token_data.get("access_level") == "ppv":
        return token_data.get("video_id") == video.get("id")
    
    return False

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, access_token: str = Cookie(None)):
    """Landing page - Netflix-style hero + carousels"""
    
    token_data = None
    if access_token:
        token_data = verify_token(access_token)
    
    videos = fetch_videos(limit=100)
    
    hero_video = None
    for v in videos:
        if check_video_access(v, token_data):
            hero_video = v
            break
    
    recent_videos = [v for v in videos if check_video_access(v, token_data)][:20]
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "hero_video": hero_video,
        "recent_videos": recent_videos,
        "is_authenticated": token_data is not None,
        "is_vip": token_data and token_data.get("access_level") == "vip",
        "environment": ENVIRONMENT,
        "is_production": IS_PRODUCTION
    })


@app.head("/", include_in_schema=False)
async def home_head(request: Request):
    """Health check for HTTP HEAD probes to the root path.

    Some platforms (Render, AWS, etc.) prefer to use an HTTP HEAD check on
    the service root. FastAPI normally adds HEAD alongside GET, but explicit
    handlers avoid 405s when proxy or middleware modifies behavior.
    """
    return PlainTextResponse("OK")

@app.get("/watch/{video_id}", response_class=HTMLResponse)
async def watch(request: Request, video_id: str, access_token: str = Cookie(None)):
    """Watch page - Video player with access control"""
    
    print(f"🎬 Accessing /watch/{video_id}")
    
    token_data = None
    if access_token:
        try:
            token_data = verify_token(access_token)
            print(f"✅ Token valid: {token_data}")
        except Exception as e:
            print(f"⚠️ Token verification failed: {e}")
    
    try:
        curator_url = f"{CURATOR_URL}/videos/{video_id}"
        print(f"📡 Fetching from: {curator_url}")
        
        response = requests.get(curator_url, timeout=10)
        print(f"📊 Curator response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Curator error: {response.text}")
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        
        video = response.json()
        print(f"✅ Video found: {video.get('title', 'N/A')}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    
    has_access = check_video_access(video, token_data)
    
    if not has_access:
        if video.get("access_level") in ["vip", "ppv"]:
            return RedirectResponse(url=f"/login?next=/watch/{video_id}", status_code=303)
    
    try:
        related_videos = fetch_videos(limit=20)
        related_videos = [
            v for v in related_videos 
            if str(v.get("id")) != str(video_id) and check_video_access(v, token_data)
        ][:6]
    except Exception as e:
        print(f"⚠️ Could not fetch related videos: {e}")
        related_videos = []
    
    bunny_video_id = video.get("bunny_video_id")
    if not bunny_video_id:
        print(f"❌ No bunny_video_id for video {video_id}")
    # Determine library type and pick library id
    library_type = video.get("library_type", "private")
    library_id = BUNNY_PUBLIC_LIBRARY_ID if library_type == "public" else BUNNY_PRIVATE_LIBRARY_ID

    # Build signed embed URL for private library or plain embed for public
    secure_embed_url = None
    try:
        if library_type == "private":
            # Use a security key to produce a signed URL (Bunny token auth)
            secure_embed_url = get_secure_embed_url(
                library_id=int(library_id),
                video_id=bunny_video_id,
                security_key=BUNNY_SECURITY_KEY,
                autoplay=True
            )
        else:
            secure_embed_url = f"https://iframe.mediadelivery.net/embed/{library_id}/{bunny_video_id}?autoplay=true"
    except Exception as e:
        print(f"⚠️ Error generating secure embed url: {e}")
        secure_embed_url = f"https://iframe.mediadelivery.net/embed/{BUNNY_PRIVATE_LIBRARY_ID}/{bunny_video_id}?autoplay=true"
    # Keep a fallback iframe URL (private library default). Public URL provided for clarity below
    iframe_url = f"https://iframe.mediadelivery.net/embed/{library_id}/{bunny_video_id}?autoplay=true"
    print(f"🎬 Iframe URL: {iframe_url}")
    # Normalize video object for template
    video["video_id"] = video.get("bunny_video_id")
    video["cdn_hostname"] = video.get("cdn_hostname") or ""

    # Map related video fields
    for rv in related_videos:
        if "video_id" not in rv and "bunny_video_id" in rv:
            rv["video_id"] = rv.get("bunny_video_id")
        if "cdn_hostname" not in rv:
            rv["cdn_hostname"] = rv.get("cdn_hostname") or ""

    return templates.TemplateResponse("watch.html", {
        "request": request,
        "video": video,
        "iframe_url": iframe_url,
        "related_videos": related_videos,
        "is_authenticated": token_data is not None,
        "is_vip": token_data and token_data.get("access_level") == "vip"
    })


def _rate_limited_embed_decorator(func):
    # Apply limiter if available
    if limiter:
        return limiter.limit("20/minute")(func)
    return func

@app.get("/api/embed/{video_id}")
@_rate_limited_embed_decorator
async def api_embed(request: Request, video_id: int, access_token: str = Cookie(None)):
    """Return signed embed URL for a video if the caller has access.

    This endpoint hides the `BUNNY_SECURITY_KEY` and only returns the signed
    url after verifying the user's access (via Monetizer), or immediately
    for public videos.
    """
    # Verify token (optional) — support cookie or Authorization header as a fallback
    token_data = None
    if access_token:
        token_data = verify_token(access_token)
    else:
        # Accept Bearer token in Authorization header (helpful for API clients)
        auth = request.headers.get('Authorization')
        if auth and auth.lower().startswith('bearer '):
            bearer = auth.split(None, 1)[1]
            token_data = verify_token(bearer)

    # Fetch video metadata from Curator
    resp = requests.get(f"{CURATOR_URL}/videos/{video_id}", timeout=10)
    if resp.status_code != 200:
        return JSONResponse({"ok": False, "error": "video_not_found"}, status_code=404)

    video = resp.json()

    # Access control
    if not check_video_access(video, token_data):
        # If no token and access restricted, instruct to login
        return JSONResponse({"ok": False, "error": "access_denied"}, status_code=401)

    bunny_video_id = video.get("bunny_video_id")
    if not bunny_video_id:
        return JSONResponse({"ok": False, "error": "video_configuration_error"}, status_code=500)

    library_type = video.get("library_type", "private")
    library_id = BUNNY_PUBLIC_LIBRARY_ID if library_type == "public" else BUNNY_PRIVATE_LIBRARY_ID

    # Generate signed URL for private library
    try:
        if library_type == "private":
            signed_url = get_secure_embed_url(library_id=int(library_id), video_id=bunny_video_id, security_key=BUNNY_SECURITY_KEY, autoplay=True)
        else:
            signed_url = f"https://iframe.mediadelivery.net/embed/{library_id}/{bunny_video_id}?autoplay=true"
    except Exception as e:
        print(f"❌ Error generating signed url: {e}")
        return JSONResponse({"ok": False, "error": "sign_error"}, status_code=500)

    # Audit log
    try:
        client_ip = request.client.host if request.client else 'unknown'
        logger.info(
            f"embed_request ip={client_ip} referer={request.headers.get('referer')} "
            f"video_id={video_id} library_id={library_id} success=True"
        )
    except Exception:
        pass

    return JSONResponse({"ok": True, "embed_url": signed_url})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page for token authentication"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/login")
async def login(request: Request):
    """Authenticate user with token"""
    data = await request.json()
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token required")
    
    # Log token type (short code vs long token) for debugging
    print(f"🔐 Login token received (len={len(token)}, sample={token[:8]})")
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    response = JSONResponse({"ok": True, "access_level": token_data.get("access_level")})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=30*24*60*60,
        samesite="lax",
        secure=IS_PRODUCTION
    )
    return response

@app.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "public_interface",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }


@app.head("/health", include_in_schema=False)
async def health_head():
    """Ensure HTTP HEAD health checks return 200 quickly.

    Some deployment platforms use HEAD on / or /health for liveness checks; by
    explicitly returning an empty success response we avoid 405 errors.
    """
    return PlainTextResponse("OK")

@app.get("/monetizer", response_class=HTMLResponse)
async def monetizer_page(request: Request):
    """Monetizer management page"""
    return templates.TemplateResponse("monetizer.html", {"request": request})

@app.get("/api/tokens")
async def get_tokens():
    """Get all tokens from Monetizer API"""
    try:
        response = requests.get(f"{MONETIZER_URL}/tokens", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching tokens: {e}")
        return {"tokens": [], "error": str(e)}

def _rate_limited_mint_decorator(func):
    if limiter:
        return limiter.limit("10/minute")(func)
    return func

@app.post("/api/tokens/mint")
@_rate_limited_mint_decorator
async def mint_token(request: Request):
    """Create new token via Monetizer API"""
    try:
        data = await request.json()
        response = requests.post(
            f"{MONETIZER_URL}/mint",
            json=data,
            timeout=10
        )
        try:
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Monetizer error status: {response.status_code} - {response.text}")
            raise HTTPException(status_code=502, detail=f"Monetizer error: {response.status_code}")

        try:
            resp_json = response.json()
        except ValueError:
            print(f"❌ Monetizer returned non-JSON: {response.text}")
            raise HTTPException(status_code=502, detail="Monetizer returned invalid response")

        # Audit log
        client_ip = request.client.host if request.client else 'unknown'
        logger.info(
            f"mint_request ip={client_ip} token_ok={resp_json.get('ok', False)} title={data.get('title')}"
        )

        return resp_json
    except HTTPException:
        # Allow HTTPExceptions raised above to propagate with their status
        raise
    except Exception as e:
        print(f"❌ Error minting token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tokens/revoke")
async def revoke_token(request: Request):
    """Revoke token via Monetizer API"""
    try:
        data = await request.json()
        response = requests.post(
            f"{MONETIZER_URL}/revoke",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error revoking token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print(f"🌐 PUBLIC INTERFACE starting on port {PORT}...")
    print(f"🚪 Gateway: {GATEWAY_URL}")
    print(f"🎬 Curator: {CURATOR_URL}")
    print(f"💰 Monetizer: {MONETIZER_URL}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
