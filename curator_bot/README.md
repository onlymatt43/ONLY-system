# 📹 Curator Bot - Bloc #1

Service de surveillance automatique des nouveaux fichiers vidéo.

## 🎯 Rôle

- Surveille un dossier local pour détecter les nouvelles vidéos
- Envoie automatiquement un événement au Gateway
- Support du scan manuel via API
- Indépendant et modulaire

## 🚀 Démarrage

```bash
cd curator_bot
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec tes paramètres
python3 curator_bot.py
```

Le service démarre sur **http://localhost:5054**

## ⚙️ Configuration (.env)

```env
PORT=5054
WATCH_DIR=./videos/input
GATEWAY_URL=http://localhost:5055/event
VIDEO_EXTENSIONS=.mp4,.mov,.mkv,.avi,.webm
```

## 🔗 API

### GET /
Status du service

### POST /scan
Scan manuel d'un dossier

```bash
curl -X POST http://localhost:5054/scan \
  -H "Content-Type: application/json" \
  -d '{"directory":"./videos/input"}'
```

## 📡 Événements envoyés

Quand une nouvelle vidéo est détectée :

```json
{
  "event": "new_video",
  "file": "/path/absolut/video.mp4",
  "timestamp": "2025-11-12T01:23:45"
}
```

→ Envoyé au Gateway via POST /event

## 🔧 Indépendance

- Aucune dépendance externe (SaaS)
- Tourne en local
- Peut être remplacé par un autre système de surveillance
- Communication HTTP uniquement
