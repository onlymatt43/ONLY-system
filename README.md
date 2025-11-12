# 🎬 ONLY - Système Netflix Modulaire

Système de publication automatisée de contenu vidéo, inspiré de Netflix, avec architecture en micro-services indépendants.

## 🎯 Philosophie

- **Modulaire** : chaque bloc est un service indépendant
- **Autonome** : minimum de dépendances externes (SaaS)
- **Low-cost** : gratuit ou très économique
- **Automatisé** : IA et bots orchestrent tout
- **Scalable** : chaque bloc peut être dupliqué/remplacé

## 🧩 Architecture

```
                    ┌─────────────────┐
                    │  Web Interface  │  (Dashboard + UI)
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼─────┐       ┌──────▼──────┐     ┌──────▼──────┐
  │  Curator  │       │   Gateway   │     │  Monetizer  │
  │    Bot    │──────>│ (Queue+DB)  │<────│     AI      │
  └───────────┘       └──────┬──────┘     └─────────────┘
                             │
                    ┌────────┼────────┐
                    │        │        │
             ┌──────▼──┐  ┌──▼────┐  ┌▼──────────┐
             │ Narrator│  │Publish│  │ Sentinel  │
             │   AI    │  │er AI  │  │ Dashboard │
             └─────────┘  └───────┘  └───────────┘
```

## 📦 Blocs (Micro-services)

| Bloc | Rôle | Port | Dépendances |
|------|------|------|-------------|
| **Web Interface** | Dashboard + Gestion complète | 5000 | Proxy vers tous les services |
| **Curator Bot** | Surveillance de nouveaux médias | 5054 | watchdog |
| **Narrator AI** | Analyse & métadonnées (IA) | 5056 | ffprobe, Ollama/OpenAI (opt.) |
| **Gateway** | Orchestrateur central + queue | 5055 | SQLite |
| **Publisher AI** | Publication réseaux sociaux | 5058 | APIs X/IG/YT (opt.) |
| **Monetizer AI** | Gestion tokens + QR codes | 5060 | SQLite |
| **Sentinel Dashboard** | Supervision temps réel | 5059 | lecture seule |

**Note:** Builder Bot (WordPress) n'est plus nécessaire avec Web Interface.

## 🚀 Démarrage rapide

### 1. Prérequis
```bash
# Python 3.9+
python3 --version

# ffmpeg (pour Narrator AI)
brew install ffmpeg  # macOS
```

### 2. Lancer tous les services

Chaque bloc dans son propre terminal :

```bash
# Terminal 1 - Gateway (démarrer en premier)
cd gateway
pip install -r requirements.txt
cp .env.example .env
python3 gateway.py

# Terminal 2 - Narrator AI
cd narrator_ai
pip install -r requirements.txt
cp .env.example .env
python3 narrator_ai.py

# Terminal 3 - Publisher AI
cd publisher_ai
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec tokens réseaux sociaux (optionnel)
python3 publisher_ai.py

# Terminal 4 - Monetizer AI
cd monetizer_ai
pip install -r requirements.txt
cp .env.example .env
python3 monetizer_ai.py

# Terminal 5 - Web Interface (interface principale)
cd web_interface
pip install -r requirements.txt
cp .env.example .env
python3 web_interface.py

# Terminal 6 - Curator Bot (optionnel - surveillance fichiers)
cd curator_bot
pip install -r requirements.txt
cp .env.example .env
python3 curator_bot.py

# Terminal 7 - Sentinel Dashboard (monitoring avancé)
cd sentinel_dashboard
pip install -r requirements.txt
cp .env.example .env
python3 sentinel.py
```

### 3. Accéder à l'interface

Ouvre **http://localhost:5000** dans ton navigateur (Web Interface principale).

Alternative : **http://localhost:5059** pour Sentinel Dashboard (monitoring).

## 🔄 Workflow complet

1. **Upload via Web Interface** → créer un job manuellement
   OU **Curator Bot** détecte une nouvelle vidéo dans `/videos/input`
2. Envoie événement au **Gateway** → job créé (status: `queued`)
3. **Gateway** appelle **Narrator AI** → génère titre, description, tags
4. **Gateway** appelle **Publisher AI** → publie sur réseaux + notif
5. Job passe en status `done` avec lien du post
6. **Monetizer AI** peut générer un token d'accès avec QR code
7. **Web Interface** & **Sentinel Dashboard** affichent tout en temps réel

## ⚙️ Configuration minimale

### Web Interface (.env)
```env
PORT=5000
GATEWAY_URL=http://localhost:5055
NARRATOR_URL=http://localhost:5056
PUBLISHER_URL=http://localhost:5058
MONETIZER_URL=http://localhost:5060
```

### Gateway (.env)
```env
PORT=5055
NARRATOR_URL=http://localhost:5056/describe
PUBLISHER_URL=http://localhost:5058/notify
```

### Monetizer AI (.env)
```env
PORT=5060
SECRET_KEY=ton-secret-super-long-et-unique
CODE_PREFIX=OM43
```

### Publisher AI (.env)
Tous les jetons sont **optionnels** :
```env
# Email
SMTP_SERVER=smtp.gmail.com
SMTP_USER=ton@email.com
SMTP_PASS=motdepasse

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789

# X/Twitter
X_BEARER_USER=eyJhbGciOiJ...

# Instagram (Business requis)
IG_USER_ID=123456789
IG_ACCESS_TOKEN=EAAG...

# YouTube
YT_CLIENT_SECRETS=./client_secret.json
```

## 📊 Monitoring

- **Web Interface** : http://localhost:5000 (interface principale)
- **Sentinel Dashboard** : http://localhost:5059 (monitoring avancé)
- **Gateway API** : http://localhost:5055/jobs
- **Services status** : http://localhost:5000/api/status

## 🔧 Indépendance

### ✅ Ce que tu possèdes
- Code source complet
- Base de données locale (SQLite)
- Logs en local
- Aucun SaaS obligatoire

### ❌ Ce qui n'est PAS requis
- ~~WordPress~~ : remplacé par Web Interface
- Metricool
- Make.com / Zapier
- Services cloud propriétaires
- Base de données externe (PostgreSQL, MySQL)

### 📡 Dépendances externes (optionnelles)
- **Ollama / OpenAI** : pour IA (fallback local disponible)
- **X / Instagram / YouTube** : pour réseaux (tous optionnels)
- **SMTP** : pour notifications email (optionnel)

## 🧱 Avantages de l'architecture

### Modularité
Chaque bloc peut être :
- Remplacé par un autre service
- Redémarré indépendamment
- Dupliqué pour load balancing
- Développé dans un autre langage

### Scalabilité
- Ajoute autant de Curators que nécessaire
- Multiple Builders pour différents sites
- Publishers pour différents comptes

### Robustesse
- Si un bloc tombe : les autres continuent
- Gateway garde la queue en SQLite
- Retry automatique sur erreurs réseau
- Idempotence : pas de double traitement

## 📚 Documentation détaillée

### Blocs principaux
- [Web Interface](web_interface/README.md) - **Interface utilisateur complète**
- [Gateway](gateway/README.md) - **Orchestrateur central**
- [Narrator AI](narrator_ai/README.md) - Analyse vidéo + IA
- [Publisher AI](publisher_ai/README.md) - Publication réseaux sociaux
- [Monetizer AI](monetizer_ai/README.md) - Gestion tokens d'accès

### Blocs secondaires
- [Curator Bot](curator_bot/README.md) - Surveillance fichiers (optionnel)
- [Sentinel Dashboard](sentinel_dashboard/README.md) - Monitoring avancé
- ~~[Builder Bot](builder_bot/README.md)~~ - WordPress (deprecated)

## 🧪 Test rapide

```bash
# Démarre tous les services puis :
cd curator_bot

# Simule l'arrivée d'une nouvelle vidéo
curl -X POST http://localhost:5055/event \
  -H "Content-Type: application/json" \
  -d '{
    "event": "new_video",
    "file": "/path/to/test.mp4",
    "timestamp": "2025-11-12T01:23:45Z"
  }'

# Vérifie le dashboard
open http://localhost:5059
```

## 🔐 Sécurité

- Application Passwords pour WordPress (pas de plugin JWT)
- Tokens OAuth2 pour réseaux sociaux
- Pas de credentials hardcodés (`.env` gitignorés)
- Lecture seule pour Sentinel Dashboard

## 🚦 Ports utilisés

- **5000** : Web Interface (interface principale) ⭐
- 5055 : Gateway (orchestrateur) 🔧
- 5056 : Narrator AI
- 5058 : Publisher AI
- 5059 : Sentinel Dashboard
- 5060 : Monetizer AI
- ~~5054 : Curator Bot~~ (optionnel)
- ~~5057 : Builder Bot~~ (deprecated)

## 🌐 Déploiement Production

### Render.com (recommandé)
Consulte [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) pour le guide complet.

**Résumé :**
- 5 services Web Services sur Render (gratuit ou $7/mois chacun)
- SQLite avec Render Disks pour persistence
- Variables d'environnement pour configuration
- Déploiement Git push automatique

### Docker (alternative)
```bash
docker-compose up -d
```
(fichier docker-compose.yml à venir)

## 📈 Prochaines étapes (optionnel)

- **Authentification** : JWT pour Web Interface
- **Analytics AI** : statistiques avancées locales
- **Storage Watcher** : surveillance NAS/Synology
- **Coach AI** : recommandations automatiques
- **Docker Compose** : déploiement one-click

## 📝 Licence

Propriétaire - Tous droits réservés

---

**Créé pour ONLY - Netflix modulaire autonome**
