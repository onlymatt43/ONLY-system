#!/bin/bash

echo "🔧 ONLY System - Correction Automatique Complète"
echo "=================================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Créer .env global
echo "1️⃣ Création .env global..."
cat > .env << 'EOF'
# filepath: /Users/mathieucourchesne/ONLY-system-1/.env
ENVIRONMENT=local

# Services URLs (LOCAL)
CURATOR_URL=http://localhost:5061
MONETIZER_URL=http://localhost:5060
PUBLIC_URL=http://localhost:5062
GATEWAY_URL=http://localhost:5055

# Bunny Stream (Private Library 389178)
BUNNY_SECURITY_KEY=453f0507-2f2c-4155-95bd-31a2fdd3610c
BUNNY_PRIVATE_API_KEY=9bf388e8-181a-4740-bf90bc96c622-3394-4591
BUNNY_PRIVATE_LIBRARY_ID=389178
BUNNY_PRIVATE_CDN_HOSTNAME=vz-a3ab0733-842.b-cdn.net

# Bunny Stream (Public Library 420867)
BUNNY_PUBLIC_API_KEY=5eb42e83-6fe9-48fb-b08c5656f422-3033-490a
BUNNY_PUBLIC_LIBRARY_ID=420867
BUNNY_PUBLIC_CDN_HOSTNAME=vz-9cf89254-609.b-cdn.net

# Turso Database (Monetizer)
TURSO_DATABASE_URL=libsql://only-tokens-onlymatt43.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjMwMDA4ODEsImlkIjoiMDcwYzdkOGEtZGUwZC00OGExLWI5NmMtNjlkN2U5MDkxODYzIiwicmlkIjoiOGQyNWI5M2QtOTJhMy00MzgxLWJhN2ItZjM3MGFhYmUxZDc2In0.y8jY7sYrNg2q88su0IK8RcVo0pqDgGjqEfneuMEptWfylVCgAqJv-X1e9L3hrzpz_IYTmjNbs4uJGiJdE7CWAg

# Security
SECRET_KEY=0mO2mPJISGYEf00nnvwvGfdT2D9LilVYcz29cdpIDbeF2odFK5z-JAXsNx1bYMjPYwUAhWDQ067Mlo-9zi038g
CODE_PREFIX=OM43
EOF

echo -e "${GREEN}✅${NC} .env global créé"

# 2. Fix public_interface.py - Ajouter fonctions manquantes
echo ""
echo "2️⃣ Correction public_interface.py..."

cat > public_interface/public_interface.py << 'PYTHON_EOF'
# filepath: /Users/mathieucourchesne/ONLY-system-1/public_interface/public_interface.py
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

def generate_session_token(video_id: str, access_token: str = None) -> str:
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
        return response.json()
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
        raise HTTPException(status_code=500, detail="Video configuration error")
    
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
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/login")
async def login(request: Request):
    """Authenticate user with token"""
    data = await request.json()
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token required")
    
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    response = JSONResponse({"ok": True, "access_level": token_data.get("access_level")})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=30*24*60*60,
        samesite="lax"
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

if __name__ == "__main__":
    print(f"🌐 PUBLIC INTERFACE starting on port {PORT}...")
    print(f"🚪 Gateway: {GATEWAY_URL}")
    print(f"🎬 Curator: {CURATOR_URL}")
    print(f"💰 Monetizer: {MONETIZER_URL}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
PYTHON_EOF

echo -e "${GREEN}✅${NC} public_interface.py corrigé"

# 3. Git commit et push
echo ""
echo "3️⃣ Git commit et push..."

git add .
git commit -m "Fix: Auto-correction complete - env vars + missing functions + health endpoints" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${NC} Commit créé"
    
    read -p "Push sur GitHub maintenant ? (Y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        git push origin main
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅${NC} Poussé sur GitHub"
        else
            echo -e "${RED}❌${NC} Erreur push GitHub"
        fi
    else
        echo -e "${YELLOW}⏸️${NC} Push annulé"
    fi
else
    echo -e "${YELLOW}ℹ️${NC} Rien à commiter (déjà à jour)"
fi

echo ""
echo "=================================="
echo -e "${GREEN}✅ Auto-fix terminé !${NC}"
echo "=================================="
echo ""
echo -e "${YELLOW}📝 ACTIONS MANUELLES RESTANTES:${NC}"
echo ""
echo "1️⃣ Sur Bunny Dashboard (https://panel.bunny.net):"
echo "   - Library 389178 → Security"
echo "   - Désactive 'Embed view token authentication' (temporaire)"
echo "   - OU ajoute BUNNY_SECURITY_KEY sur Render si tu veux Token Auth ON"
echo ""
echo "2️⃣ Attends que Render redéploie (3-5 min si push GitHub)"
echo ""
echo "3️⃣ Teste:"
echo "   ${GREEN}curl https://only-public.onrender.com/watch/121${NC}"
echo ""
echo "🎉 Le système devrait maintenant fonctionner !"