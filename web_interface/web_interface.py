import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import requests
from typing import Dict, Any

load_dotenv()

PORT = int(os.getenv("PORT", "5000"))

# URLs des services (à configurer selon environnement)
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5055")
NARRATOR_URL = os.getenv("NARRATOR_URL", "http://localhost:5056")
BUILDER_URL = os.getenv("BUILDER_URL", "http://localhost:5057")
PUBLISHER_URL = os.getenv("PUBLISHER_URL", "http://localhost:5058")
SENTINEL_URL = os.getenv("SENTINEL_URL", "http://localhost:5059")
MONETIZER_URL = os.getenv("MONETIZER_URL", "http://localhost:5060")
CURATOR_URL = os.getenv("CURATOR_URL", "http://localhost:5061")

app = FastAPI(title="ONLY Web Interface", version="1.0")

# Monter les fichiers statiques et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil principale"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "gateway_url": GATEWAY_URL,
        "services": {
            "gateway": GATEWAY_URL,
            "narrator": NARRATOR_URL,
            "builder": BUILDER_URL,
            "publisher": PUBLISHER_URL,
            "sentinel": SENTINEL_URL,
            "monetizer": MONETIZER_URL
        }
    })


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Page d'upload de vidéos"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """Page de gestion des jobs"""
    return templates.TemplateResponse("jobs.html", {"request": request})


@app.get("/monetizer", response_class=HTMLResponse)
async def monetizer_page(request: Request):
    """Page de gestion des tokens"""
    return templates.TemplateResponse("monetizer.html", {"request": request})


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Page d'analytics"""
    return templates.TemplateResponse("analytics.html", {"request": request})


@app.get("/curator", response_class=HTMLResponse)
async def curator_page(request: Request):
    """Page de curation des vidéos"""
    return templates.TemplateResponse("curator.html", {"request": request})


# === API Proxy endpoints (pour éviter CORS) ===

@app.get("/api/status")
async def check_services_status():
    """Vérifie l'état de tous les services"""
    services = {}
    
    for name, url in [
        ("gateway", GATEWAY_URL),
        ("narrator", NARRATOR_URL),
        ("builder", BUILDER_URL),
        ("publisher", PUBLISHER_URL),
        ("sentinel", SENTINEL_URL),
        ("monetizer", MONETIZER_URL)
    ]:
        try:
            r = requests.get(f"{url}/", timeout=3)
            services[name] = {
                "status": "online" if r.status_code == 200 else "error",
                "code": r.status_code
            }
        except Exception as e:
            services[name] = {
                "status": "offline",
                "error": str(e)
            }
    
    return services


@app.get("/api/jobs")
async def get_jobs(limit: int = 50):
    """Récupère la liste des jobs depuis le Gateway"""
    try:
        r = requests.get(f"{GATEWAY_URL}/jobs?limit={limit}", timeout=10)
        r.raise_for_status()
        data = r.json()
        
        # Ensure we return an array
        if isinstance(data, dict) and "error" in data:
            return []
        if not isinstance(data, list):
            return []
        
        return data
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []


@app.post("/api/upload")
async def trigger_upload(request: Request):
    """Déclenche le traitement d'une vidéo"""
    data = await request.json()
    try:
        r = requests.post(f"{GATEWAY_URL}/event", json=data, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/monetizer/mint")
async def mint_token(request: Request):
    """Crée un nouveau token d'accès"""
    data = await request.json()
    try:
        r = requests.post(f"{MONETIZER_URL}/mint", json=data, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/monetizer/tokens")
async def get_tokens(limit: int = 50):
    """Récupère la liste des tokens"""
    try:
        r = requests.get(f"{MONETIZER_URL}/tokens?limit={limit}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/curator/videos")
async def get_curator_videos(limit: int = 50, offset: int = 0):
    """Récupère les vidéos du Curator"""
    try:
        r = requests.get(f"{CURATOR_URL}/videos?limit={limit}&offset={offset}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/curator/categories")
async def get_curator_categories():
    """Récupère les catégories"""
    try:
        r = requests.get(f"{CURATOR_URL}/categories", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/curator/categories")
async def create_curator_category(request: Request):
    """Crée une nouvelle catégorie"""
    data = await request.json()
    try:
        r = requests.post(f"{CURATOR_URL}/categories", json=data, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/curator/sync")
async def sync_curator_videos():
    """Synchronise les vidéos depuis Bunny"""
    try:
        r = requests.post(f"{CURATOR_URL}/sync/bunny", timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
def health():
    return {"status": "ok", "service": "web_interface"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
