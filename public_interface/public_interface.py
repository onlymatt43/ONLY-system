#!/usr/bin/env python3
"""
PUBLIC INTERFACE - ONLY System
Interface publique client Netflix-style pour viewers/subscribers
Port: 5062
"""

import os
import requests
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from bunny_signer import get_secure_embed_url
from dotenv import load_dotenv
import hmac
import hashlib
import time

# Configuration
PORT = int(os.getenv("PORT", "5062"))

# ✅ FIX: Charge .env depuis racine projet ET dossier courant
load_dotenv()  # Charge .env dossier courant
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))  # Charge .env racine

# Environment detection
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')
IS_PRODUCTION = ENVIRONMENT == 'production'

# ✅ FIX: Service URLs avec defaults
CURATOR_URL = os.environ.get('CURATOR_URL', 'http://localhost:5061')
MONETIZER_URL = os.environ.get('MONETIZER_URL', 'http://localhost:5060')
GATEWAY_URL = os.environ.get('GATEWAY_URL', 'http://localhost:5055')  # ✅ AJOUTÉ

# Bunny Security
BUNNY_SECURITY_KEY = os.environ.get('BUNNY_SECURITY_KEY')

if not BUNNY_SECURITY_KEY:
    print("⚠️ BUNNY_SECURITY_KEY non configurée")

app = FastAPI(title="ONLY - Public Interface", version="1.0.0")

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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
        return response.json()
    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []

def fetch_categories():
    """Fetch categories from Curator Bot"""
    try:
        response = requests.get(f"{CURATOR_URL}/categories", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching categories: {e}")
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
    # Public videos: everyone
    if video.get("access_level") == "public":
        return True
    
    # No token = no access to restricted content
    if not token_data:
        return False
    
    # VIP token: access to VIP + PPV content
    if token_data.get("access_level") == "vip":
        return True
    
    # PPV token: only specific video
    if token_data.get("access_level") == "ppv":
        return token_data.get("video_id") == video.get("id")
    
    return False

def generate_session_token(video_id: str, access_token: str = None) -> str:
    """Generate temporary session token for video access"""
    timestamp = int(time.time())
    data = f"{video_id}:{timestamp}:{access_token or 'anon'}"
    
    # Sign with secret key
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
        
        # Check expiration
        if time.time() - timestamp > max_age_seconds:
            return False
        
        # Verify signature would require storing original access_token
        # For now, just check format and expiry
        return len(signature) == 16
        
    except (ValueError, AttributeError):
        return False

# ============================================================================
# PUBLIC ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, access_token: str = Cookie(None)):
    """Landing page - Netflix-style hero + carousels"""
    
    # Verify token if present
    token_data = None
    if access_token:
        token_data = verify_token(access_token)
    
    # Fetch content
    videos = fetch_videos(limit=100)
    categories = fetch_categories()
    
    # Hero video (first public or user-accessible video)
    hero_video = None
    for v in videos:
        if check_video_access(v, token_data):
            hero_video = v
            break
    
    # Group videos by category for carousels
    category_carousels = []
    for cat in categories:
        cat_videos = [v for v in videos if cat["id"] in v.get("category_ids", []) and check_video_access(v, token_data)]
        if cat_videos:
            category_carousels.append({
                "category": cat,
                "videos": cat_videos[:20]  # Max 20 per carousel
            })
    
    # Recent uploads (accessible to user)
    recent_videos = [v for v in videos if check_video_access(v, token_data)][:20]
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "hero_video": hero_video,
        "category_carousels": category_carousels,
        "recent_videos": recent_videos,
        "is_authenticated": token_data is not None,
        "is_vip": token_data and token_data.get("access_level") == "vip",
        "environment": ENVIRONMENT,  # Ajoute ça
        "is_production": IS_PRODUCTION
    })

@app.get("/browse", response_class=HTMLResponse)
async def browse(request: Request, category: str = None, tag: str = None, access_token: str = Cookie(None)):
    """Browse page - Full grid with filters"""
    
    # Verify token
    token_data = None
    if access_token:
        token_data = verify_token(access_token)
    
    # Fetch content
    videos = fetch_videos(limit=200)
    categories = fetch_categories()
    
    # Filter accessible videos
    accessible_videos = [v for v in videos if check_video_access(v, token_data)]
    
    # Apply filters
    if category:
        accessible_videos = [v for v in accessible_videos if category in v.get("category_ids", [])]
    if tag:
        accessible_videos = [v for v in accessible_videos if tag in v.get("tag_ids", [])]
    
    return templates.TemplateResponse("browse.html", {
        "request": request,
        "videos": accessible_videos,
        "categories": categories,
        "selected_category": category,
        "is_authenticated": token_data is not None,
        "is_vip": token_data and token_data.get("access_level") == "vip"
    })

@app.get("/watch/{video_id}", response_class=HTMLResponse)
async def watch(request: Request, video_id: str, access_token: str = Cookie(None)):
    """Watch page - Video player with access control"""
    
    print(f"🎬 Accessing /watch/{video_id}")
    
    # Verify token
    token_data = None
    if access_token:
        try:
            token_data = verify_token(access_token)
            print(f"✅ Token valid: {token_data}")
        except Exception as e:
            print(f"⚠️ Token verification failed: {e}")
    
    # Fetch video details from Curator
    try:
        curator_url = f"{CURATOR_URL}/videos/{video_id}"
        print(f"📡 Fetching from: {curator_url}")
        
        response = requests.get(curator_url, timeout=10)
        print(f"📊 Curator response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Curator error: {response.text}")
            raise HTTPException(
                status_code=404,
                detail=f"Video {video_id} not found"
            )
        
        video = response.json()
        print(f"✅ Video found: {video.get('title', 'N/A')}")
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Cannot connect to Curator: {e}")
        raise HTTPException(
            status_code=503,
            detail="Curator service unavailable"
        )
    except requests.exceptions.Timeout:
        print(f"❌ Curator timeout")
        raise HTTPException(
            status_code=504,
            detail="Request timeout"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
    
    # Check access
    has_access = check_video_access(video, token_data)
    
    if not has_access:
        if video.get("access_level") in ["vip", "ppv"]:
            return RedirectResponse(
                url=f"/login?next=/watch/{video_id}",
                status_code=303
            )
    
    # Fetch related videos
    try:
        related_videos = fetch_videos(limit=20)
        related_videos = [
            v for v in related_videos 
            if str(v.get("id")) != str(video_id) and check_video_access(v, token_data)
        ][:6]
    except Exception as e:
        print(f"⚠️ Could not fetch related videos: {e}")
        related_videos = []
    
    # Generate simple iframe URL (Token Auth désactivé sur Bunny)
    bunny_video_id = video.get("bunny_video_id")
    if not bunny_video_id:
        print(f"❌ No bunny_video_id for video {video_id}")
        raise HTTPException(
            status_code=500,
            detail="Video configuration error"
        )
    
    # Simple iframe URL (Token Auth désactivé sur Bunny)
    iframe_url = f"https://iframe.mediadelivery.net/embed/389178/{bunny_video_id}?autoplay=true"
    
    print(f"🎬 Iframe URL: {iframe_url}")
    
    return templates.TemplateResponse("watch.html", {
        "request": request,
        "video": video,
        "iframe_url": iframe_url,
        "related_videos": related_videos,
        "is_authenticated": token_data is not None,
        "is_vip": token_data and token_data.get("access_level") == "vip"
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page for token authentication"""
    return templates.TemplateResponse("login.html", {
        "request": request
    })

@app.post("/api/login")
async def login(request: Request):
    """Authenticate user with token"""
    data = await request.json()
    token = data.get("token")
    
    if not token:
        # Verify token with Monetizer
        raise HTTPException(status_code=400, detail="Token required")
    
    # Verify token with Monetizer
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Return success with token to set as cookie
    response = JSONResponse({"ok": True, "access_level": token_data.get("access_level")})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=30*24*60*60,  # 30 days
        samesite="lax"
    )
    return response

@app.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

# ============================================================================
# API ENDPOINTS (for AJAX)
# ============================================================================

@app.get("/api/videos")
async def api_videos(category_id: str = None, tag_id: str = None, limit: int = 50, access_token: str = Cookie(None)):
    """API endpoint for videos with access control"""
    token_data = None
    if access_token:
        token_data = verify_token(access_token)
    
    videos = fetch_videos(category_id=category_id, tag_id=tag_id, limit=limit)
    accessible_videos = [v for v in videos if check_video_access(v, token_data)]
    return accessible_videos

@app.get("/api/categories")
async def api_categories():
    """API endpoint for categories"""
    return fetch_categories()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "public_interface",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN
# ============================================================================

print(f"🌐 PUBLIC INTERFACE starting on port {PORT}...")

if __name__ == "__main__":
    print(f"🌐 PUBLIC INTERFACE starting on port {PORT}...")
    print(f"🚪 Gateway: {GATEWAY_URL}")
    print(f"🎬 Curator: {CURATOR_URL}")
    print(f"💰 Monetizer: {MONETIZER_URL}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)