"""
Curator Bot - Intelligence éditoriale du système ONLY

Fonctionnalités :
- Sync avec Bunny Stream API (fetch vidéos existantes)
- Gestion de métadonnées (tags, catégories, séries, access)
- Upload de nouvelles vidéos (YouTube download + fichiers locaux)
- Système de curation dynamique (filtres, tri, recommandations)
- CRUD complet pour catégories/tags/séries
"""

import os
import sqlite3
import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", "5061"))
DB_PATH = os.getenv("DB_PATH", "./curator.db")

# Bunny Stream API
BUNNY_API_KEY = os.getenv("BUNNY_API_KEY", "")
BUNNY_LIBRARY_ID = os.getenv("BUNNY_LIBRARY_ID", "389178")
BUNNY_CDN_HOSTNAME = os.getenv("BUNNY_CDN_HOSTNAME", "vz-a3ab0733-842.b-cdn.net")
BUNNY_API_BASE = f"https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}"

app = FastAPI(title="Curator Bot", version="1.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure DB directory exists
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def db():
    """Return database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with all required tables"""
    conn = db()
    c = conn.cursor()
    
    # Videos table (Bunny Stream metadata + custom metadata)
    c.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bunny_video_id TEXT UNIQUE,
        guid TEXT,
        title TEXT,
        description TEXT,
        duration INTEGER,
        thumbnail_url TEXT,
        video_url TEXT,
        status TEXT DEFAULT 'active',
        access_level TEXT DEFAULT 'public',
        views INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT,
        bunny_data TEXT
    )""")
    
    # Categories table
    c.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        slug TEXT UNIQUE,
        color TEXT,
        icon TEXT,
        description TEXT,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    
    # Tags table
    c.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        slug TEXT UNIQUE,
        created_at TEXT
    )""")
    
    # Series table
    c.execute("""
    CREATE TABLE IF NOT EXISTS series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        slug TEXT UNIQUE,
        description TEXT,
        thumbnail_url TEXT,
        created_at TEXT
    )""")
    
    # Video-Category associations (many-to-many)
    c.execute("""
    CREATE TABLE IF NOT EXISTS video_categories (
        video_id INTEGER,
        category_id INTEGER,
        PRIMARY KEY (video_id, category_id),
        FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    )""")
    
    # Video-Tag associations (many-to-many)
    c.execute("""
    CREATE TABLE IF NOT EXISTS video_tags (
        video_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (video_id, tag_id),
        FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    )""")
    
    # Video-Series association (one-to-many)
    c.execute("""
    CREATE TABLE IF NOT EXISTS video_series (
        video_id INTEGER,
        series_id INTEGER,
        episode_number INTEGER,
        PRIMARY KEY (video_id),
        FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
        FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
    )""")
    
    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_access ON videos(access_level)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_bunny ON videos(bunny_video_id)")
    
    conn.commit()
    conn.close()
    logger.info(f"[DB] Initialized: {DB_PATH}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUNNY STREAM API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def bunny_headers():
    """Return Bunny API headers"""
    return {
        "AccessKey": BUNNY_API_KEY,
        "Content-Type": "application/json"
    }


def fetch_bunny_videos(page: int = 1, items_per_page: int = 100) -> Dict[str, Any]:
    """Fetch videos from Bunny Stream API"""
    url = f"{BUNNY_API_BASE}/videos"
    params = {"page": page, "itemsPerPage": items_per_page}
    
    try:
        response = requests.get(url, headers=bunny_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching Bunny videos: {e}")
        return {"items": [], "totalItems": 0}


def get_bunny_video(video_id: str) -> Optional[Dict[str, Any]]:
    """Get single video from Bunny Stream API"""
    url = f"{BUNNY_API_BASE}/videos/{video_id}"
    
    try:
        response = requests.get(url, headers=bunny_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching Bunny video {video_id}: {e}")
        return None


def upload_to_bunny(title: str, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Upload video to Bunny Stream"""
    # Create video object first
    url = f"{BUNNY_API_BASE}/videos"
    data = {"title": title}
    
    try:
        response = requests.post(url, headers=bunny_headers(), json=data, timeout=10)
        response.raise_for_status()
        video_data = response.json()
        
        # If file_path provided, upload the file
        if file_path and os.path.exists(file_path):
            video_id = video_data.get("guid")
            upload_url = f"{BUNNY_API_BASE}/videos/{video_id}"
            
            with open(file_path, 'rb') as f:
                upload_response = requests.put(
                    upload_url,
                    headers={"AccessKey": BUNNY_API_KEY},
                    data=f,
                    timeout=300
                )
                upload_response.raise_for_status()
        
        return video_data
    except Exception as e:
        logger.error(f"Error uploading to Bunny: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE OPERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def sync_video_from_bunny(bunny_video: Dict[str, Any]) -> int:
    """Sync a video from Bunny Stream to local DB"""
    conn = db()
    c = conn.cursor()
    
    # Add cdn_hostname column if it doesn't exist (migration)
    try:
        c.execute("ALTER TABLE videos ADD COLUMN cdn_hostname TEXT")
        conn.commit()
    except:
        pass  # Column already exists
    
    bunny_video_id = bunny_video.get("guid")
    title = bunny_video.get("title", "Untitled")
    duration = bunny_video.get("length", 0)
    thumbnail_url = bunny_video.get("thumbnailFileName", "")
    
    # Build video URL
    video_url = f"https://{BUNNY_CDN_HOSTNAME}/{bunny_video_id}/playlist.m3u8"
    
    # Check if video exists
    existing = c.execute("SELECT id FROM videos WHERE bunny_video_id = ?", (bunny_video_id,)).fetchone()
    
    if existing:
        # Update
        c.execute("""
            UPDATE videos SET 
                title = ?, duration = ?, thumbnail_url = ?, 
                video_url = ?, cdn_hostname = ?, bunny_data = ?, updated_at = ?
            WHERE bunny_video_id = ?
        """, (title, duration, thumbnail_url, video_url, BUNNY_CDN_HOSTNAME, json.dumps(bunny_video), now_utc(), bunny_video_id))
        video_id = existing["id"]
    else:
        # Insert
        c.execute("""
            INSERT INTO videos (bunny_video_id, guid, title, duration, thumbnail_url, 
                                video_url, cdn_hostname, bunny_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bunny_video_id, bunny_video_id, title, duration, thumbnail_url, 
              video_url, BUNNY_CDN_HOSTNAME, json.dumps(bunny_video), now_utc(), now_utc()))
        video_id = c.lastrowid
    
    conn.commit()
    conn.close()
    return video_id


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CATEGORIES CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_category(name: str, color: str = "#666", icon: str = "📁", description: str = "") -> int:
    """Create a new category"""
    conn = db()
    c = conn.cursor()
    slug = name.lower().replace(" ", "-")
    c.execute("""
        INSERT INTO categories (name, slug, color, icon, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, slug, color, icon, description, now_utc()))
    category_id = c.lastrowid
    conn.commit()
    conn.close()
    return category_id


def get_all_categories() -> List[Dict[str, Any]]:
    """Get all categories"""
    conn = db()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM categories ORDER BY sort_order, name").fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_event("startup")
async def startup():
    init_db()
    logger.info(f"[Curator Bot] Started on port {PORT}")


@app.get("/")
async def home():
    return {
        "service": "Curator Bot",
        "version": "1.0",
        "status": "running",
        "bunny_configured": bool(BUNNY_API_KEY)
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/sync/bunny")
async def sync_bunny_videos():
    """Sync all videos from Bunny Stream API"""
    logger.info("[Sync] Starting Bunny Stream sync...")
    
    page = 1
    total_synced = 0
    
    while True:
        result = fetch_bunny_videos(page=page)
        videos = result.get("items", [])
        
        if not videos:
            break
        
        for video in videos:
            try:
                sync_video_from_bunny(video)
                total_synced += 1
            except Exception as e:
                logger.error(f"Error syncing video {video.get('guid')}: {e}")
        
        # Check if more pages
        if len(videos) < 100:
            break
        page += 1
    
    logger.info(f"[Sync] Completed. Synced {total_synced} videos")
    return {"ok": True, "synced": total_synced}


@app.get("/videos")
async def list_videos(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    series: Optional[str] = None,
    access: Optional[str] = None
):
    """List videos with filters"""
    conn = db()
    c = conn.cursor()
    
    query = "SELECT * FROM videos WHERE status = 'active'"
    params = []
    
    if access:
        query += " AND access_level = ?"
        params.append(access)
    
    # TODO: Add category/tag/series filtering with JOINs
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


@app.get("/videos/{video_id}")
async def get_video(video_id: int):
    """Get single video with full metadata"""
    conn = db()
    c = conn.cursor()
    
    video = c.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not video:
        return JSONResponse({"error": "Video not found"}, status_code=404)
    
    # Get categories
    categories = c.execute("""
        SELECT c.* FROM categories c
        JOIN video_categories vc ON c.id = vc.category_id
        WHERE vc.video_id = ?
    """, (video_id,)).fetchall()
    
    # Get tags
    tags = c.execute("""
        SELECT t.* FROM tags t
        JOIN video_tags vt ON t.id = vt.tag_id
        WHERE vt.video_id = ?
    """, (video_id,)).fetchall()
    
    conn.close()
    
    result = dict(video)
    result["categories"] = [dict(c) for c in categories]
    result["tags"] = [dict(t) for t in tags]
    
    return result


@app.post("/categories")
async def create_category_endpoint(request: Request):
    """Create new category"""
    data = await request.json()
    name = data.get("name")
    color = data.get("color", "#666")
    icon = data.get("icon", "📁")
    description = data.get("description", "")
    
    if not name:
        return JSONResponse({"error": "Name required"}, status_code=400)
    
    try:
        category_id = create_category(name, color, icon, description)
        return {"ok": True, "category_id": category_id}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/categories")
async def list_categories():
    """List all categories"""
    return get_all_categories()


@app.post("/videos/{video_id}/categories")
async def assign_category(video_id: int, request: Request):
    """Assign category to video"""
    data = await request.json()
    category_id = data.get("category_id")
    
    conn = db()
    c = conn.cursor()
    
    try:
        c.execute("""
            INSERT OR IGNORE INTO video_categories (video_id, category_id)
            VALUES (?, ?)
        """, (video_id, category_id))
        conn.commit()
        conn.close()
        return {"ok": True}
    except Exception as e:
        conn.close()
        return JSONResponse({"error": str(e)}, status_code=400)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
