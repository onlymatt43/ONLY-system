# 📣 Publisher AI - Bloc #5

Service de publication automatique sur les réseaux sociaux et notifications.

## 🎯 Rôle

- Envoie des notifications (email, Telegram)
- Publie sur X/Twitter (API v2)
- Publie sur Instagram Business (Graph API)
- Upload sur YouTube (Data API)
- **ZÉRO dépendance à Metricool, Make, Zapier**
- API directes uniquement

## 🚀 Démarrage

```bash
cd publisher_ai
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec tes tokens
python3 publisher_ai.py
```

Le service démarre sur **http://localhost:5058**

## ⚙️ Configuration (.env)

### Email (SMTP)
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ton@email.com
SMTP_PASS=motdepasseapp
NOTIFY_TO=destinataire@email.com
```

### Telegram
```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

### X/Twitter
```env
X_BEARER_USER=eyJhbGciOiJ...  # OAuth2 User Access Token
X_API_POST=https://api.twitter.com/2/tweets
```

**Comment obtenir:**
1. developer.twitter.com → Create App
2. OAuth 2.0 → scope `tweet.write`
3. Récupère Access Token

### Instagram
```env
IG_USER_ID=123456789           # ID compte Business
IG_ACCESS_TOKEN=EAAG...        # Long-lived token
IG_API_BASE=https://graph.facebook.com/v19.0
```

**Prérequis:**
- Compte Instagram **Business**
- Connecté à une Page Facebook
- Long-lived token Graph API

### YouTube
```env
YT_CLIENT_SECRETS=./client_secret.json
YT_CREDENTIALS=./yt_token.json
YT_DEFAULT_PRIVACY=unlisted    # public|unlisted|private
```

**Prérequis:**
1. Google Cloud Console → Create OAuth Client (Desktop)
2. Download `client_secret.json`
3. Premier run → navigateur s'ouvre pour autorisation
4. Token sauvegardé dans `yt_token.json`

## 🔗 API

### GET /
Status du service

### POST /notify
Envoie notifications email + Telegram

```bash
curl -X POST http://localhost:5058/notify \
  -H "Content-Type: application/json" \
  -d '{"title":"New Episode","link":"https://..."}'
```

### POST /social/publish
Publie sur tous les réseaux configurés

```bash
curl -X POST http://localhost:5058/social/publish \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Shadows in Motion",
    "description": "Une exploration poétique...",
    "link": "https://example.com/video",
    "image_url": "https://cdn.example.com/poster.jpg",
    "video_url": "https://cdn.example.com/video.mp4",
    "local_video_path": "/videos/input/scene1.mov"
  }'
```

**Réponse:**
```json
{
  "ok": true,
  "results": {
    "x": {"ok": true, "status": 201, "resp": {...}},
    "instagram": {"ok": true, "id": "17895..."},
    "youtube": {"ok": true, "video_id": "dQw4w9WgXcQ", "watch": "https://youtu.be/..."}
  }
}
```

## 🧱 Fonctionnalités

- **X (Twitter)** : post texte + lien
- **Instagram** : post image OU vidéo (URL publique requise)
- **YouTube** : upload fichier local avec titre/description
- **Fallback gracieux** : si token manquant → skip sans erreur

## 🔧 Indépendance

- **Aucun SaaS** : Metricool, Make, Zapier non requis
- API officielles directes
- Tokens stockés localement
- Peut tourner n'importe où (VPS, local, Docker)
- Communication HTTP uniquement

## 📝 Notes

- X nécessite OAuth2 avec `tweet.write`
- Instagram requiert compte Business + Page Facebook
- YouTube : premier run ouvre navigateur (OAuth)
- Tous les services sont optionnels : configure seulement ceux que tu veux
