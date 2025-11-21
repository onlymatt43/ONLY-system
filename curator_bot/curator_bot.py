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

# ✅ FIX: Charge .env global ET local
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configuration
PORT = int(os.environ.get("PORT", 5061))
DB_PATH = os.getenv("DB_PATH", "./curator.db")

# Bunny Stream API - PRIVATE Library (full videos)
BUNNY_PRIVATE_API_KEY = os.getenv("BUNNY_PRIVATE_API_KEY", "9bf388e8-181a-4740-bf90bc96c622-3394-4591")
BUNNY_PRIVATE_LIBRARY_ID = os.getenv("BUNNY_PRIVATE_LIBRARY_ID", "389178")
BUNNY_PRIVATE_CDN_HOSTNAME = os.getenv("BUNNY_PRIVATE_CDN_HOSTNAME", "vz-a3ab0733-842.b-cdn.net")

# Bunny Stream API - PUBLIC Library (previews/posts)
BUNNY_PUBLIC_API_KEY = os.getenv("BUNNY_PUBLIC_API_KEY", "5eb42e83-6fe9-48fb-b08c5656f422-3033-490a")
BUNNY_PUBLIC_LIBRARY_ID = os.getenv("BUNNY_PUBLIC_LIBRARY_ID", "420867")
BUNNY_PUBLIC_CDN_HOSTNAME = os.getenv("BUNNY_PUBLIC_CDN_HOSTNAME", "vz-9cf89254-609.b-cdn.net")

# Legacy variables (keep for backward compatibility)
BUNNY_API_KEY = BUNNY_PRIVATE_API_KEY
BUNNY_LIBRARY_ID = BUNNY_PRIVATE_LIBRARY_ID
BUNNY_CDN_HOSTNAME = BUNNY_PRIVATE_CDN_HOSTNAME
BUNNY_API_BASE = f"https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}"

app = FastAPI(title="Curator Bot", version="1.0")

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
        library_type TEXT DEFAULT 'private',
        views INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT,
        bunny_data TEXT,
        cdn_hostname TEXT
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUNNY STREAM API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_library_config(library_type: str = "private") -> Dict[str, str]:
    """Get library configuration (ID, CDN hostname, API key)"""
    if library_type == "public":
        return {
            "api_key": BUNNY_PUBLIC_API_KEY,
            "library_id": BUNNY_PUBLIC_LIBRARY_ID,
            "cdn_hostname": BUNNY_PUBLIC_CDN_HOSTNAME,
            "api_base": f"https://video.bunnycdn.com/library/{BUNNY_PUBLIC_LIBRARY_ID}"
        }
    else:  # private (default)
        return {
            "api_key": BUNNY_PRIVATE_API_KEY,
            "library_id": BUNNY_PRIVATE_LIBRARY_ID,
            "cdn_hostname": BUNNY_PRIVATE_CDN_HOSTNAME,
            "api_base": f"https://video.bunnycdn.com/library/{BUNNY_PRIVATE_LIBRARY_ID}"
        }


def bunny_headers(library_type: str = "private"):
    """Return Bunny API headers for specific library"""
    config = get_library_config(library_type)
    return {
        "AccessKey": config["api_key"],
        "Content-Type": "application/json"
    }


def fetch_bunny_videos(page: int = 1, items_per_page: int = 100, library_type: str = "private") -> Dict[str, Any]:
    """Fetch videos from Bunny Stream API"""
    config = get_library_config(library_type)
    url = f"{config['api_base']}/videos"
    params = {"page": page, "itemsPerPage": items_per_page}
    
    try:
        response = requests.get(url, headers=bunny_headers(library_type), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Bunny videos ({library_type}): {e}")
        return {"items": [], "totalItems": 0}


def get_bunny_video(video_id: str, library_type: str = "private") -> Optional[Dict[str, Any]]:
    """Get single video from Bunny Stream API"""
    config = get_library_config(library_type)
    url = f"{config['api_base']}/videos/{video_id}"
    
    try:
        response = requests.get(url, headers=bunny_headers(library_type), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Bunny video {video_id} ({library_type}): {e}")
        return None


def upload_to_bunny(title: str, file_path: Optional[str] = None, library_type: str = "private") -> Optional[Dict[str, Any]]:
    """Upload video to Bunny Stream"""
    config = get_library_config(library_type)
    url = f"{config['api_base']}/videos"
    data = {"title": title}
    
    try:
        response = requests.post(url, headers=bunny_headers(library_type), json=data, timeout=10)
        response.raise_for_status()
        video_data = response.json()
        
        # If file_path provided, upload the file
        if file_path and os.path.exists(file_path):
            video_id = video_data.get("guid")
            upload_url = f"{config['api_base']}/videos/{video_id}"
            
            with open(file_path, 'rb') as f:
                upload_response = requests.put(
                    upload_url,
                    headers={"AccessKey": config["api_key"]},
                    data=f,
                    timeout=300
                )
                upload_response.raise_for_status()
        
        return video_data
    except Exception as e:
        print(f"Error uploading to Bunny ({library_type}): {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE OPERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def sync_video_from_bunny(bunny_video: Dict[str, Any], library_type: str = "private") -> int:
    """Sync a video from Bunny Stream to local DB"""
    conn = db()
    c = conn.cursor()
    
    # Add library_type column if it doesn't exist (migration)
    try:
        c.execute("ALTER TABLE videos ADD COLUMN library_type TEXT DEFAULT 'private'")
        conn.commit()
    except:
        pass  # Column already exists
    
    config = get_library_config(library_type)
    cdn_hostname = config["cdn_hostname"]
    
    bunny_video_id = bunny_video.get("guid")
    title = bunny_video.get("title", "Untitled")
    duration = bunny_video.get("length", 0)
    thumbnail_url = bunny_video.get("thumbnailFileName", "")
    
    # Build video URL
    video_url = f"https://{cdn_hostname}/{bunny_video_id}/playlist.m3u8"
    
    # Check if video exists
    existing = c.execute("SELECT id FROM videos WHERE bunny_video_id = ?", (bunny_video_id,)).fetchone()
    
    if existing:
        # Update
        c.execute("""
            UPDATE videos SET 
                title = ?, duration = ?, thumbnail_url = ?, 
                video_url = ?, cdn_hostname = ?, library_type = ?, bunny_data = ?, updated_at = ?
            WHERE bunny_video_id = ?
        """, (title, duration, thumbnail_url, video_url, cdn_hostname, library_type, json.dumps(bunny_video), now_utc(), bunny_video_id))
        video_id = existing["id"]
    else:
        # Insert
        c.execute("""
            INSERT INTO videos (bunny_video_id, guid, title, duration, thumbnail_url, 
                                video_url, cdn_hostname, library_type, bunny_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bunny_video_id, bunny_video_id, title, duration, thumbnail_url, 
              video_url, cdn_hostname, library_type, json.dumps(bunny_video), now_utc(), now_utc()))
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
    print(f"[Curator Bot] Started on port {PORT}")


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
async def sync_bunny_videos(library_type: Optional[str] = None):
    """Sync videos from Bunny Stream API
    
    Args:
        library_type: "private", "public", or None (sync both)
    """
    libraries_to_sync = []
    
    if library_type:
        libraries_to_sync = [library_type]
    else:
        libraries_to_sync = ["private", "public"]
    
    total_synced = 0
    results = {}
    
    for lib_type in libraries_to_sync:
        print(f"[Sync] Starting {lib_type.upper()} library sync...")
        lib_synced = 0
        page = 1
        
        while True:
            result = fetch_bunny_videos(page=page, library_type=lib_type)
            videos = result.get("items", [])
            
            if not videos:
                break
            
            for video in videos:
                try:
                    sync_video_from_bunny(video, library_type=lib_type)
                    lib_synced += 1
                    total_synced += 1
                except Exception as e:
                    print(f"Error syncing video {video.get('guid')} ({lib_type}): {e}")
            
            # Check if more pages
            if len(videos) < 100:
                break
            page += 1
        
        results[lib_type] = lib_synced
        print(f"[Sync] {lib_type.upper()} completed: {lib_synced} videos")
    
    print(f"[Sync] Total synced: {total_synced} videos")
    return {"ok": True, "total_synced": total_synced, "details": results}


@app.get("/videos")
async def list_videos(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    series: Optional[str] = None,
    access: Optional[str] = None,
    library: Optional[str] = None
):
    """List videos with filters
    
    Args:
        library: "private" or "public" to filter by library type
    """
    conn = db()
    c = conn.cursor()
    
    query = "SELECT * FROM videos WHERE status = 'active'"
    params = []
    
    if access:
        query += " AND access_level = ?"
        params.append(access)
    
    if library:
        query += " AND library_type = ?"
        params.append(library)
    
    # TODO: Add category/tag/series filtering with JOINs
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


@app.get("/videos/{video_id}")
async def get_video(video_id: int):
    """Get specific video by ID"""
    print(f"🔍 Fetching video {video_id}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, bunny_video_id, duration, thumbnail_url,
               video_url, cdn_hostname, access_level, library_type,
               view_count, created_at
        FROM videos
        WHERE id = ?
    """, (video_id,))
    
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Video {video_id} not found in database")
        
        # List available IDs for debugging
        cursor.execute("SELECT COUNT(*) FROM videos")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM videos ORDER BY id DESC LIMIT 10")
        available = [r[0] for r in cursor.fetchall()]
        
        print(f"📊 Total videos in DB: {total}")
        print(f"📋 Available video IDs (last 10): {available}")
        
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Video {video_id} not found",
                "total_videos": total,
                "sample_ids": available,
                "hint": "Run POST /sync/bunny to import videos from Bunny Stream"
            }
        )
    
    video = {
        "id": row[0],
        "title": row[1],
        "bunny_video_id": row[2],
        "duration": row[3],
        "thumbnail_url": row[4],
        "video_url": row[5],
        "cdn_hostname": row[6],
        "access_level": row[7],
        "library_type": row[8],
        "view_count": row[9],
        "created_at": row[10]
    }
    
    print(f"✅ Video found: {video['title']}")
    return video


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
