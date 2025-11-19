import os
import json
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()

PORT = int(os.getenv("PORT", "5056"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "local")  # local|openai|anthropic
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "llama2")  # pour Ollama

app = FastAPI(title="Narrator AI", version="1.0")


def get_video_info(file_path: str) -> Dict[str, Any]:
    """Extrait les métadonnées techniques de la vidéo avec ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # Extraire infos vidéo
            video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
            format_info = data.get("format", {})
            
            return {
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "bitrate": int(format_info.get("bit_rate", 0)),
                "width": video_stream.get("width") if video_stream else None,
                "height": video_stream.get("height") if video_stream else None,
                "codec": video_stream.get("codec_name") if video_stream else None,
                "fps": eval(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0
            }
    except Exception as e:
        print(f"[Narrator] ⚠️ Erreur ffprobe: {e}")
        return {}


def generate_description_local(file_name: str, video_info: Dict) -> Dict[str, Any]:
    """Génère une description basique sans IA externe (mode fallback)"""
    
    # Extraction du titre depuis le nom de fichier
    title = Path(file_name).stem.replace("_", " ").replace("-", " ").title()
    
    # Génération simple de tags basés sur le titre
    words = title.lower().split()
    tags = [w for w in words if len(w) > 3][:5]
    
    duration_min = int(video_info.get("duration", 0) / 60)
    
    description = f"Une création visuelle de {duration_min} minutes. "
    
    if "art" in title.lower() or "nude" in title.lower():
        description += "Exploration artistique subtile, contemplative et poétique."
        tags.extend(["art", "fine art", "artistic"])
    elif "motion" in title.lower():
        description += "Mouvement hypnotique capturé avec précision."
        tags.extend(["motion", "slow motion"])
    else:
        description += "Une expérience visuelle unique."
    
    return {
        "title": title[:95],
        "description": description,
        "tags": list(set(tags))[:10],
        "category": "Art",
        "file": file_name
    }


def generate_description_ollama(file_name: str, video_info: Dict) -> Dict[str, Any]:
    """Génère une description avec Ollama (local AI)"""
    try:
        prompt = f"""Tu es un expert en création de contenu artistique. Analyse ce fichier vidéo et génère :

Fichier: {Path(file_name).stem}
Durée: {int(video_info.get('duration', 0) / 60)} minutes
Résolution: {video_info.get('width')}x{video_info.get('height')}

Génère un JSON avec :
- title: titre captivant (max 95 caractères)
- description: description poétique et engageante (2-3 phrases)
- tags: 5-8 tags pertinents
- category: catégorie (Art, Documentary, Experimental, etc.)

Réponds UNIQUEMENT avec le JSON, rien d'autre."""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": LOCAL_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("response", "")
            
            # Nettoyer et parser le JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            data["file"] = file_name
            return data
            
    except Exception as e:
        print(f"[Narrator] ⚠️ Ollama error: {e}")
    
    # Fallback
    return generate_description_local(file_name, video_info)


def generate_description_openai(file_name: str, video_info: Dict) -> Dict[str, Any]:
    """Génère une description avec OpenAI GPT"""
    if not OPENAI_API_KEY:
        return generate_description_local(file_name, video_info)
    
    try:
        prompt = f"""Analyze this video file and create engaging metadata:

File: {Path(file_name).stem}
Duration: {int(video_info.get('duration', 0) / 60)} minutes
Resolution: {video_info.get('width')}x{video_info.get('height')}

Generate a JSON with:
- title: captivating title (max 95 chars)
- description: poetic, engaging description (2-3 sentences)
- tags: 5-8 relevant tags (array of strings)
- category: category name (Art, Documentary, etc.)

Return ONLY the JSON, nothing else."""

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            
            data = json.loads(content)
            data["file"] = file_name
            return data
            
    except Exception as e:
        print(f"[Narrator] ⚠️ OpenAI error: {e}")
    
    return generate_description_local(file_name, video_info)


@app.post("/describe")
async def describe_video(request: Request):
    """Analyse une vidéo et génère ses métadonnées"""
    data = await request.json()
    file_path = data.get("file")
    
    if not file_path or not os.path.exists(file_path):
        return {"error": "File not found", "file": file_path}
    
    print(f"[Narrator] 🧠 Analyse de: {file_path}")
    
    # 1. Extraction métadonnées techniques
    video_info = get_video_info(file_path)
    
    # 2. Génération description selon le provider
    if AI_PROVIDER == "openai":
        metadata = generate_description_openai(file_path, video_info)
    elif AI_PROVIDER == "ollama":
        metadata = generate_description_ollama(file_path, video_info)
    else:
        metadata = generate_description_local(file_path, video_info)
    
    # 3. Ajout des infos techniques
    metadata["video_info"] = video_info
    metadata["file"] = file_path
    
    print(f"[Narrator] ✅ Métadonnées générées: {metadata.get('title')}")
    
    return metadata


@app.get("/")
def index():
    return {
        "status": "Narrator AI online",
        "provider": AI_PROVIDER,
        "model": LOCAL_MODEL if AI_PROVIDER == "ollama" else "N/A"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "narrator_ai",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
