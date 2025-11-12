# 🧠 Narrator AI - Bloc #2

Service d'analyse et génération de métadonnées pour les vidéos.

## 🎯 Rôle

- Analyse les fichiers vidéo (durée, résolution, codec, etc.)
- Génère titre, description et tags
- Support multiple IA : local (fallback), Ollama, OpenAI, Anthropic
- Indépendant et modulaire

## 🚀 Démarrage

```bash
cd narrator_ai
pip install -r requirements.txt

# Installer ffprobe (si pas déjà installé)
brew install ffmpeg  # macOS

cp .env.example .env
# Éditer .env avec tes paramètres
python3 narrator_ai.py
```

Le service démarre sur **http://localhost:5056**

## ⚙️ Configuration (.env)

```env
PORT=5056
AI_PROVIDER=local        # local|ollama|openai|anthropic
LOCAL_MODEL=llama2       # si ollama
OPENAI_API_KEY=          # si openai
```

## 🔗 API

### GET /
Status du service

### POST /describe
Analyse une vidéo et génère les métadonnées

```bash
curl -X POST http://localhost:5056/describe \
  -H "Content-Type: application/json" \
  -d '{"file":"/path/to/video.mp4"}'
```

**Réponse:**

```json
{
  "title": "Shadows in Motion",
  "description": "Une exploration poétique de la lumière et du mouvement. Subtil, hypnotique, contemplatif.",
  "tags": ["art nude", "slow motion", "black and white", "fine art"],
  "category": "Art",
  "file": "/path/to/video.mp4",
  "video_info": {
    "duration": 180.5,
    "width": 1920,
    "height": 1080,
    "codec": "h264",
    "fps": 24
  }
}
```

## 🤖 Modes IA

### Local (fallback)
- Aucune dépendance externe
- Génération basique basée sur le nom de fichier
- Toujours disponible

### Ollama
- IA locale via Ollama
- Gratuit, privé, pas de limite
- Nécessite Ollama installé: `ollama run llama2`

### OpenAI
- GPT-4 pour descriptions riches
- Coût par requête
- Nécessite clé API

## 🔧 Indépendance

- Fonctionne hors ligne (mode local)
- Pas de dépendance cloud obligatoire
- Peut être remplacé par un autre système d'IA
- Communication HTTP uniquement
