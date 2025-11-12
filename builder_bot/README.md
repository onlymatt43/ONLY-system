# 📦 Builder Bot - Bloc #3

Service de création de posts WordPress via REST API.

## 🎯 Rôle

- Crée des posts WordPress avec métadonnées
- Gère les catégories et tags (création auto si inexistant)
- Upload d'images à la une (featured media)
- Support Presto Player ou balise video HTML5
- Support paywall (membres, tokens)
- Indépendant et modulaire

## 🚀 Démarrage

```bash
cd builder_bot
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec tes infos WordPress
python3 builder_bot.py
```

Le service démarre sur **http://localhost:5057**

## ⚙️ Configuration (.env)

### WordPress
Utilise les **Application Passwords** (WP 5.6+) :
1. WP Admin → Users → ton user → Application Passwords
2. Add New → copie la clé
3. Auth = Basic (user : app_password)

```env
WP_URL=https://example.com
WP_USER=editor_username
WP_APP_PASS=xxxx xxxx xxxx xxxx xxxx xxxx
DEFAULT_STATUS=publish
DEFAULT_CATEGORY=Series
```

### Lecteur vidéo

**Option A - Presto Player (recommandé)**
```env
PRESTO_PLAYER_ID=123
```

**Option B - URL directe**
```env
VIDEO_URL_FIELD=om43_video_url
POSTER_URL_FIELD=om43_poster_url
```

### Paywall
```env
PAYWALL_MODE=free     # free|members|token
ACCESS_TAG_VIP=vip
```

## 🔗 API

### GET /
Status du service

### POST /build
Crée un post WordPress

```bash
curl -X POST http://localhost:5057/build \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Shadows in Motion",
    "description": "Une exploration poétique...",
    "tags": ["art nude", "slow motion", "intimacy"],
    "category": "Art",
    "presto_player_id": 123,
    "poster_url": "https://cdn.example.com/posters/scene1.jpg",
    "file": "/videos/input/scene1.mov",
    "status": "publish"
  }'
```

**Réponse:**

```json
{
  "ok": true,
  "post_id": 456,
  "link": "https://example.com/shadows-in-motion",
  "status": "publish",
  "featured_media": 789,
  "category_id": 5,
  "tags": [12, 34, 56]
}
```

## 🧱 Fonctionnalités

- **Catégories/Tags** : création auto si inexistants
- **Featured Image** : upload direct depuis URL
- **Presto Player** : insertion via shortcode
- **Paywall** : marquage pour plugins de restriction
- **Retry** : 3 tentatives automatiques en cas d'erreur

## 🔧 Indépendance

- Aucune dépendance externe (sauf WordPress)
- Application Passwords (pas de plugin JWT)
- Service isolé, peut tourner n'importe où
- Communication HTTP uniquement
