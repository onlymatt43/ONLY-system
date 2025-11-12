import os
import time
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

load_dotenv()

WATCH_DIR = os.getenv("WATCH_DIR", "./videos/input")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5055/event")
VIDEO_EXTENSIONS = os.getenv("VIDEO_EXTENSIONS", ".mp4,.mov,.mkv,.avi,.webm").split(",")
PORT = int(os.getenv("PORT", "5054"))

app = FastAPI(title="Curator Bot", version="1.0")

class VideoHandler(FileSystemEventHandler):
    """Surveille les nouveaux fichiers vidéo"""
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        if not isinstance(event, FileCreatedEvent):
            return
            
        file_path = event.src_path
        ext = Path(file_path).suffix.lower()
        
        if ext not in VIDEO_EXTENSIONS:
            return
        
        print(f"[Curator] 🎬 Nouveau fichier détecté: {file_path}")
        
        # Attendre que le fichier soit complètement écrit
        time.sleep(2)
        
        # Envoyer l'événement au Gateway
        try:
            payload = {
                "event": "new_video",
                "file": os.path.abspath(file_path),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            r = requests.post(GATEWAY_URL, json=payload, timeout=10)
            
            if r.status_code in (200, 201):
                print(f"[Curator] ✅ Événement envoyé au Gateway: {file_path}")
            else:
                print(f"[Curator] ⚠️ Erreur Gateway ({r.status_code}): {r.text[:200]}")
                
        except Exception as e:
            print(f"[Curator] ❌ Erreur lors de l'envoi: {e}")

# Observer watchdog
observer = None

@app.on_event("startup")
def start_watcher():
    global observer
    
    # Créer le répertoire si inexistant
    Path(WATCH_DIR).mkdir(parents=True, exist_ok=True)
    
    print(f"[Curator] 👀 Surveillance du dossier: {os.path.abspath(WATCH_DIR)}")
    print(f"[Curator] 📹 Extensions surveillées: {VIDEO_EXTENSIONS}")
    
    observer = Observer()
    observer.schedule(VideoHandler(), WATCH_DIR, recursive=True)
    observer.start()
    
    print(f"[Curator] 🚀 Curator Bot démarré sur le port {PORT}")

@app.on_event("shutdown")
def stop_watcher():
    if observer:
        observer.stop()
        observer.join()

@app.get("/")
def index():
    return {
        "status": "Curator Bot online",
        "watching": os.path.abspath(WATCH_DIR),
        "extensions": VIDEO_EXTENSIONS,
        "gateway": GATEWAY_URL
    }

@app.post("/scan")
async def manual_scan(request: Request):
    """Scan manuel du dossier surveillé"""
    data = await request.json()
    directory = data.get("directory", WATCH_DIR)
    
    files_found = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in VIDEO_EXTENSIONS:
                file_path = os.path.join(root, file)
                files_found.append(file_path)
                
                try:
                    payload = {
                        "event": "new_video",
                        "file": os.path.abspath(file_path),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    requests.post(GATEWAY_URL, json=payload, timeout=10)
                except Exception as e:
                    print(f"[Curator] Erreur scan: {e}")
    
    return {"ok": True, "files_found": len(files_found), "files": files_found}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
