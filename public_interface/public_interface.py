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

# Configuration
PORT = int(os.getenv("PORT", "5062"))
CURATOR_URL = os.getenv("CURATOR_URL", "http://localhost:5061")
MONETIZER_URL = os.getenv("MONETIZER_URL", "http://localhost:5060")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5055")

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
        "is_vip": token_data and token_data.get("access_level") == "vip"
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
    
    # Import Bunny signer for secure embed URLs
    try:
        from bunny_signer import get_secure_embed_url
        use_signed_urls = True
    except Exception as e:
        print(f"Warning: bunny_signer not available: {e}")
        use_signed_urls = False
    
    # Verify token
    token_data = None
    if access_token:
        token_data = verify_token(access_token)
    
    # Fetch video details from Curator
    try:
        response = requests.get(f"{CURATOR_URL}/videos/{video_id}", timeout=5)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Video not found")
        video = response.json()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check access
    has_access = check_video_access(video, token_data)
    
    if not has_access:
        # SECURITY: Don't render watch.html with iframe if no access
        # Redirect to login instead of showing paywall with video metadata
        if video.get("access_level") in ["vip", "ppv"]:
            # Redirect to login page with return URL
            return RedirectResponse(url=f"/login?next=/watch/{video_id}", status_code=303)
    
    # Fetch related videos
    related_videos = fetch_videos(limit=20)
    related_videos = [v for v in related_videos if v["id"] != video_id and check_video_access(v, token_data)][:6]
    
    # Generate secure embed URL if signing is available
    if use_signed_urls:
        try:
            secure_embed_url = get_secure_embed_url(
                library_id="389178",
                video_id=video["bunny_video_id"],
                autoplay=True,
                expires_in=7200  # 2 hours
            )
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            # Fallback to simple URL
            secure_embed_url = f"https://iframe.mediadelivery.net/embed/389178/{video['bunny_video_id']}?autoplay=true&muted=false&loop=false&preload=true"
    else:
        # Simple URL without token
        secure_embed_url = f"https://iframe.mediadelivery.net/embed/389178/{video['bunny_video_id']}?autoplay=true&muted=false&loop=false&preload=true"
    
    return templates.TemplateResponse("watch.html", {
        "request": request,
        "video": video,
        "secure_embed_url": secure_embed_url,
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

if __name__ == "__main__":
    print(f"🌐 PUBLIC INTERFACE starting on port {PORT}...")
    print(f"🎬 Curator: {CURATOR_URL}")
    print(f"💰 Monetizer: {MONETIZER_URL}")
    print(f"🚪 Gateway: {GATEWAY_URL}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
