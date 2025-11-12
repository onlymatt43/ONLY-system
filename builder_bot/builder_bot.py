import os
import base64
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import requests
from tenacity import retry, wait_fixed, stop_after_attempt

load_dotenv()

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASS = os.getenv("WP_APP_PASS", "")
DEFAULT_STATUS = os.getenv("DEFAULT_STATUS", "publish")
DEFAULT_AUTHOR_ID = int(os.getenv("DEFAULT_AUTHOR_ID", "0")) or None
DEFAULT_CATEGORY = os.getenv("DEFAULT_CATEGORY", "Series")

PRESTO_PLAYER_ID = os.getenv("PRESTO_PLAYER_ID", "")
VIDEO_URL_FIELD = os.getenv("VIDEO_URL_FIELD", "om43_video_url")
POSTER_URL_FIELD = os.getenv("POSTER_URL_FIELD", "om43_poster_url")

PAYWALL_MODE = os.getenv("PAYWALL_MODE", "free")  # free|members|token
ACCESS_TAG_VIP = os.getenv("ACCESS_TAG_VIP", "vip")

PORT = int(os.getenv("PORT", "5057"))

app = FastAPI(title="Builder Bot", version="1.0")


# ---------- Helpers ----------
def _auth_headers() -> Dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASS}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }


def _wp(endpoint: str) -> str:
    return f"{WP_URL}/wp-json/wp/v2/{endpoint.lstrip('/')}"


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
def _get(url: str, params: Dict[str, Any] = None):
    r = requests.get(url, headers=_auth_headers(), params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
def _post(url: str, payload: Dict[str, Any]):
    r = requests.post(
        url,
        headers=_auth_headers(),
        data=json.dumps(payload),
        timeout=30
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"POST {url} -> {r.status_code} {r.text[:500]}")
    return r.json()


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
def _media_upload(image_url: str) -> Optional[int]:
    """Téléverse une image distante en media WP et retourne son media ID"""
    try:
        img = requests.get(image_url, timeout=20)
        img.raise_for_status()
        
        fname = image_url.split("/")[-1] or "poster.jpg"
        
        headers = _auth_headers()
        headers.update({
            "Content-Disposition": f'attachment; filename="{fname}"',
            "Content-Type": img.headers.get("Content-Type", "image/jpeg")
        })
        
        url = f"{WP_URL}/wp-json/wp/v2/media"
        r = requests.post(url, headers=headers, data=img.content, timeout=30)
        
        if r.status_code in (200, 201):
            return r.json().get("id")
        return None
    except Exception:
        return None


def _ensure_category(name: str) -> int:
    # Cherche
    try:
        cats = _get(_wp("categories"), params={"search": name})
        for c in cats:
            if c.get("name", "").lower() == name.lower():
                return c["id"]
    except Exception:
        pass
    
    # Crée
    created = _post(_wp("categories"), {"name": name})
    return created["id"]


def _ensure_tag(name: str) -> int:
    try:
        tags = _get(_wp("tags"), params={"search": name})
        for t in tags:
            if t.get("name", "").lower() == name.lower():
                return t["id"]
    except Exception:
        pass
    
    created = _post(_wp("tags"), {"name": name})
    return created["id"]


def build_content_block(p: Dict[str, Any]) -> str:
    """Génère le contenu HTML du post"""
    title = p.get("title") or ""
    desc = p.get("description") or ""
    presto_id = str(p.get("presto_player_id") or PRESTO_PLAYER_ID or "").strip()
    video_url = p.get("video_url", "")
    poster_url = p.get("poster_url", "")
    
    blocks = []
    
    if presto_id:
        blocks.append(f'[presto_player id="{presto_id}"]')
    elif video_url:
        poster_attr = f' poster="{poster_url}"' if poster_url else ""
        blocks.append(
            f'<video controls playsinline preload="metadata"{poster_attr} style="width:100%;max-width:1400px;">'
            f'  <source src="{video_url}" type="application/x-mpegURL"/>'
            f'  <source src="{video_url}" type="video/mp4"/>'
            f'</video>'
        )
    
    if desc:
        blocks.append(f'<div class="entry-summary"><p>{desc}</p></div>')
    
    # Mini détails
    details = []
    if p.get("file"):
        details.append(f'File: <code>{p["file"]}</code>')
    if video_url:
        details.append(f'Video: <a href="{video_url}" target="_blank" rel="noopener">source</a>')
    if poster_url:
        details.append(f'Poster: <a href="{poster_url}" target="_blank" rel="noopener">image</a>')
    
    if details:
        blocks.append('<hr>' + '<br>'.join(details))
    
    return "\n\n".join(blocks)


def apply_paywall_mode(payload: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """Applique la stratégie de paywall"""
    meta = payload.setdefault("meta", {})
    
    if mode == "members":
        payload.setdefault("tags", [])
        payload["tags"].append(ACCESS_TAG_VIP)
    elif mode == "token":
        meta["requires_token"] = True
    
    return payload


@app.post("/build")
async def build_post(data: Dict[str, Any]):
    """Reçoit JSON avec métadonnées et crée le post WordPress"""
    
    if not (WP_URL and WP_USER and WP_APP_PASS):
        return {
            "error": "WP credentials missing in .env (WP_URL, WP_USER, WP_APP_PASS)"
        }
    
    title = data.get("title") or "Untitled"
    status = data.get("status") or DEFAULT_STATUS
    author = data.get("author_id") or DEFAULT_AUTHOR_ID
    
    tags_in = data.get("tags", []) or []
    category_name = data.get("category") or DEFAULT_CATEGORY
    
    # Applique le mode d'accès
    data = apply_paywall_mode(data, PAYWALL_MODE)
    
    # Catégorie
    cat_id = _ensure_category(category_name)
    
    # Tags
    tag_ids = []
    for t in tags_in:
        try:
            tag_ids.append(_ensure_tag(t))
        except Exception:
            pass
    
    # Contenu
    content = build_content_block(data)
    
    # Media à la une
    featured_media_id = None
    poster_url = data.get("poster_url") or ""
    if poster_url:
        featured_media_id = _media_upload(poster_url)
    
    # Champs meta
    meta_fields = data.get("meta", {})
    if data.get("video_url"):
        meta_fields[VIDEO_URL_FIELD] = data["video_url"]
    if poster_url and not featured_media_id:
        meta_fields[POSTER_URL_FIELD] = poster_url
    
    payload = {
        "title": title,
        "status": status,
        "content": content,
        "categories": [cat_id],
        "tags": tag_ids,
        "meta": meta_fields
    }
    
    if author:
        payload["author"] = author
    if featured_media_id:
        payload["featured_media"] = featured_media_id
    
    created = _post(_wp("posts"), payload)
    
    return {
        "ok": True,
        "post_id": created.get("id"),
        "link": created.get("link"),
        "status": created.get("status"),
        "featured_media": featured_media_id,
        "category_id": cat_id,
        "tags": tag_ids
    }


@app.get("/")
def index():
    return {
        "status": "BuilderBot online",
        "wp": WP_URL,
        "mode": PAYWALL_MODE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
