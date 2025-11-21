# 🎬 ONLY - Plateforme Vidéo Premium

Plateforme de contenu vidéo premium avec modèle freemium : previews publiques gratuits et vidéos complètes pour abonnés.

## 🎯 Philosophie

- **Freemium** : previews publics gratuits + contenu premium payant
- **Modulaire** : chaque service est indépendant et scalable
- **Sécurisé** : authentification par tokens, vidéos protégées
- **Low-cost** : Bunny CDN + Render.com free tier
- **Automatisé** : gestion de contenu simplifiée

## 🧩 Architecture

```
                    ┌──────────────────┐
                    │ Public Interface │  (Site public)
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼─────┐       ┌──────▼──────┐     ┌──────▼──────┐
  │  Curator  │       │  Monetizer  │     │  Sentinel   │
  │    Bot    │       │     AI      │     │     AI      │
  └───────────┘       └─────────────┘     └─────────────┘
       │                     │                    │
       │              (Token Auth)         (Monitoring)
       │                     │                    │
  ┌────▼──────────────────────▼────────────────────▼────┐
  │              Bunny Stream CDN                        │
  │  ┌──────────────────┐  ┌──────────────────┐         │
  │  │  Public Library  │  │  Private Library │         │
  │  │  (14 previews)   │  │  (121 videos)    │         │
  │  │  Free access     │  │  Token required  │         │
  │  └──────────────────┘  └──────────────────┘         │
  └──────────────────────────────────────────────────────┘
```

## 📦 Services Déployés

| Service | Rôle | URL Production | Status |
|---------|------|----------------|--------|
| **Public Interface** | Site web public + previews | https://only-public.onrender.com | ✅ Live |
| **Curator Bot** | Gestion vidéos Bunny (dual library) | https://only-curator.onrender.com | ✅ Live |
| **Monetizer AI** | Authentification tokens + QR codes | https://only-monetizer.onrender.com | ✅ Live |
| **Sentinel AI** | Monitoring système + alertes | https://only-sentinel.onrender.com | ✅ Live |

## 🎥 Bunny Stream - Architecture Dual Library

### Public Library (420867)
- **14 vidéos** - Previews gratuits pour tous
- **CDN**: `vz-9cf89254-609.b-cdn.net`
- **Accès**: Public, pas d'authentification
- **Usage**: Partage réseaux sociaux, découverte contenu

### Private Library (389178)
- **121 vidéos** - Contenu premium complet
- **CDN**: `vz-a3ab0733-842.b-cdn.net`
- **Accès**: Token requis, URL signées
- **Sécurité**: Token authentication ON, direct URL access blocked
 
**NOTE**: Si Token Authentication est activé pour la private library (389178), ajoute la variable d'environnement `BUNNY_SECURITY_KEY` sur le service `only-public` (Render) et localement (`.env`) pour que la `public_interface` puisse générer des URLs signées via `bunny_signer.py`.

## 🚀 Développement Local

### 1. Prérequis
```bash
# Python 3.9+
python3 --version

# Environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 2. Lancer les services essentiels

```bash
# Terminal 1 - Curator Bot
cd curator_bot
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec tes clés Bunny
python curator_bot.py

# Terminal 2 - Monetizer AI
cd monetizer_ai
pip install -r requirements.txt
cp .env.example .env
python monetizer_ai.py

# Terminal 3 - Public Interface
cd public_interface
pip install -r requirements.txt
cp .env.example .env
python public_interface.py

# Terminal 4 - Sentinel AI (monitoring)
cd sentinel_ai
pip install -r requirements.txt
cp .env.example .env
python sentinel.py
```

### 3. Accéder à l'interface

- **Site public** : http://localhost:5062
- **Monitoring** : http://localhost:10000
- **API Curator** : http://localhost:5061
- **API Monetizer** : http://localhost:5060

## 🔄 Workflow Freemium

1. **Visiteur arrive sur le site** → voit les previews publics gratuits
2. **Clique sur "Watch Full Video"** → redirigé vers authentification
3. **Entre son token** → Monetizer valide l'accès
4. **Token valide** → accès au player avec vidéo privée (URL signée)
5. **Token invalide/expiré** → reste sur previews publics
6. **Partage social** → previews publics partagés automatiquement

## ⚙️ Configuration

### Curator Bot (.env)
```env
PORT=5061

# Private Library (vidéos complètes)
BUNNY_PRIVATE_API_KEY=ta-cle-api-private
BUNNY_PRIVATE_LIBRARY_ID=389178
BUNNY_PRIVATE_CDN_HOSTNAME=vz-a3ab0733-842.b-cdn.net

# Public Library (previews gratuits)
BUNNY_PUBLIC_API_KEY=ta-cle-api-public
BUNNY_PUBLIC_LIBRARY_ID=420867
BUNNY_PUBLIC_CDN_HOSTNAME=vz-9cf89254-609.b-cdn.net
```

### Monetizer AI (.env)
```env
PORT=5060
SECRET_KEY=ton-secret-super-long-et-unique
CODE_PREFIX=OM43
TOKEN_EXPIRY_DAYS=365
```

### Public Interface (.env)
```env
PORT=5062
CURATOR_URL=http://localhost:5061
MONETIZER_URL=http://localhost:5060
SITE_NAME=ONLY
```

### Sentinel AI (.env)
```env
PORT=10000
CURATOR_URL=http://localhost:5061
MONETIZER_URL=http://localhost:5060
PUBLIC_URL=http://localhost:5062
MONITOR_INTERVAL_SEC=30
```

## 📊 APIs & Monitoring

### Curator Bot API
```bash
# Sync toutes les vidéos depuis Bunny
curl -X POST http://localhost:5061/sync/bunny

# Sync uniquement public library
curl -X POST http://localhost:5061/sync/bunny?library_type=public

# Lister vidéos publiques
curl http://localhost:5061/videos?library=public&limit=10

# Lister vidéos privées
curl http://localhost:5061/videos?library=private&limit=10
```

### Monetizer API
```bash
# Vérifier un token
curl -X POST http://localhost:5060/verify \
  -H "Content-Type: application/json" \
  -d '{"token":"OM43-XXXX-XXXX"}'

# Générer un nouveau token
curl -X POST http://localhost:5060/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","plan":"premium"}'
```

### Sentinel AI
- **Dashboard** : http://localhost:10000
- **System Health** : http://localhost:10000/api/system/health
- **Services Status** : http://localhost:10000/api/services

## 🔧 Stack Technique

### ✅ Technologies utilisées
- **Python 3.9+** : Backend services (FastAPI, Flask)
- **SQLite** : Base de données locale
- **Bunny CDN** : Streaming vidéo (2 libraries)
- **Render.com** : Hosting (free tier)
- **HTML/CSS/JS** : Frontend vanilla

### 📡 Dépendances externes
- **Bunny Stream** : CDN vidéo ($5/TB streaming)
- **Render.com** : Hosting gratuit avec auto-sleep

## 🔐 Sécurité

### Vidéos Privées
- **Token Authentication** : Bunny Stream token auth activé
- **Direct URL Block** : Accès direct aux URLs bloqué
- **Signed URLs** : URLs temporaires avec expiration
- **Token Validation** : Monetizer vérifie chaque accès

### Tokens Utilisateur
- **Format** : `OM43-XXXX-XXXX` (préfixe personnalisable)
- **Expiration** : 365 jours par défaut
- **QR Codes** : Génération automatique pour partage
- **Base de données** : SQLite local, pas de cloud

## � Ports Services

- **5061** : Curator Bot (gestion vidéos)
- **5060** : Monetizer AI (auth tokens)
- **5062** : Public Interface (site web)
- **10000** : Sentinel AI (monitoring)

## 📚 Documentation

### Services Principaux
- [Curator Bot](curator_bot/README.md) - Gestion vidéos Bunny dual library
- [Monetizer AI](monetizer_ai/README.md) - Authentification & tokens
- [Public Interface](public_interface/README.md) - Site web public
- [Sentinel AI](sentinel_ai/README.md) - Monitoring système

### Documentation Technique
- [BUNNY_DUAL_LIBRARY.md](BUNNY_DUAL_LIBRARY.md) - Architecture dual library détaillée
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) - Guide déploiement production

## 🌐 Production (Render.com)

### Services Déployés
```bash
# Curator Bot
https://only-curator.onrender.com
Status: ✅ 135 videos (14 public + 121 private)

# Monetizer AI
https://only-monetizer.onrender.com
Status: ✅ Token auth active

# Public Interface
https://only-public.onrender.com
Status: ✅ Site web live

# Sentinel AI
https://only-sentinel.onrender.com
Status: ✅ Monitoring 4 services
```

### Déploiement Automatique
- **Git Push** → Auto-deploy sur Render
- **Free Tier** : Services dorment après 15min inactivité
- **Wake Time** : ~30s au premier accès
- **Persistence** : SQLite avec Render Disks

Consulte [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) pour configuration complète.

## 📊 Statistiques Actuelles

- **135 vidéos totales** sur Bunny Stream
  - 14 previews publics (library 420867)
  - 121 vidéos privées (library 389178)
- **4 services** déployés en production
- **100% uptime** monitoring par Sentinel AI
- **$0/mois** sur Render free tier

## 📈 Roadmap

### À venir
- [ ] Signed URLs pour vidéos privées (sécurité accrue)
- [ ] Frontend : filtrage par library sur Public Interface
- [ ] Frontend : login flow + player vidéos privées
- [ ] Analytics : tracking vues par vidéo
- [ ] Social : partage automatique previews

### Améliorations futures
- [ ] Payment integration (Stripe)
- [ ] Email notifications (nouveaux contenus)
- [ ] Mobile app (PWA)
- [ ] Admin dashboard (gestion contenus)

## 📝 Licence

Propriétaire - Tous droits réservés

---

**ONLY - Plateforme vidéo premium freemium**  
*Previews gratuits pour tous • Contenu complet pour abonnés*
