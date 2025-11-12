# 🎯 ONLY - Guide de Démarrage Rapide

## ⚡ TL;DR (Trop Long; Pas Lu)

### Local (Développement)
```bash
# Démarre tout en une commande
./start_all.sh

# Ouvre le navigateur
open http://localhost:5000

# Pour arrêter
./stop_all.sh
```

### Production (Render)
Suis [RENDER_CHECKLIST.md](RENDER_CHECKLIST.md) pas à pas.

---

## 🎬 C'est Quoi ONLY ?

Un système **Netflix-style** pour :
1. **Analyser** des vidéos avec l'IA
2. **Publier** automatiquement sur les réseaux sociaux
3. **Monétiser** avec des tokens d'accès
4. **Surveiller** tout en temps réel

**Sans WordPress. Sans Zapier. Sans Make. Sans services externes payants.**

---

## 📦 Ce Que Tu As Maintenant

7 micro-services indépendants :

| Service | Rôle | URL Locale |
|---------|------|------------|
| **Web Interface** | Dashboard principal | http://localhost:5000 |
| **Gateway** | Orchestrateur + Queue | http://localhost:5055 |
| **Narrator AI** | Analyse vidéo + IA | http://localhost:5056 |
| **Publisher AI** | Publication réseaux | http://localhost:5058 |
| **Monetizer AI** | Tokens + QR codes | http://localhost:5060 |
| **Sentinel** | Monitoring avancé | http://localhost:5059 |
| **Curator Bot** | Surveillance fichiers | http://localhost:5054 |

---

## 🚀 Installation Locale

### 1. Prérequis
```bash
# Python 3.9+
python3 --version

# ffmpeg (pour analyse vidéo)
brew install ffmpeg  # macOS
# ou apt install ffmpeg  # Linux

# tmux (pour start_all.sh)
brew install tmux  # macOS
```

### 2. Configuration Services Essentiels

**Gateway** (obligatoire) :
```bash
cd gateway
cp .env.example .env
# Éditer .env si besoin (par défaut OK)
pip install -r requirements.txt
```

**Narrator AI** (obligatoire) :
```bash
cd narrator_ai
cp .env.example .env
pip install -r requirements.txt
```

**Publisher AI** (optionnel - réseaux sociaux) :
```bash
cd publisher_ai
cp .env.example .env
# Éditer .env avec tes tokens X/IG/YouTube
pip install -r requirements.txt
```

**Monetizer AI** (obligatoire) :
```bash
cd monetizer_ai
cp .env.example .env
# Change SECRET_KEY dans .env
pip install -r requirements.txt
```

**Web Interface** (obligatoire) :
```bash
cd web_interface
cp .env.example .env
pip install -r requirements.txt
```

### 3. Démarre Tout

#### Option A : Script automatique (recommandé)
```bash
./start_all.sh
```

#### Option B : Manuellement (débogage)
```bash
# Terminal 1
cd gateway && python3 gateway.py

# Terminal 2
cd narrator_ai && python3 narrator_ai.py

# Terminal 3
cd publisher_ai && python3 publisher_ai.py

# Terminal 4
cd monetizer_ai && python3 monetizer_ai.py

# Terminal 5
cd web_interface && python3 web_interface.py
```

### 4. Teste
```bash
# Ouvre le navigateur
open http://localhost:5000

# Ou lance le script de test
./test_system.sh
```

---

## 🌐 Déploiement Production (Render.com)

### Checklist Complète
Suis [RENDER_CHECKLIST.md](RENDER_CHECKLIST.md) pour un guide détaillé.

### Résumé Ultra-Rapide
1. Push ton code sur GitHub
2. Crée 5 Web Services sur Render
3. Configure les variables d'environnement
4. Ajoute des Disks pour Gateway & Monetizer
5. Attends 10min → C'est prêt !

**Coût :** 0$/mois (gratuit) ou 35$/mois (production)

---

## 🎯 Workflow Utilisateur

### Scénario 1 : Upload Manuel
1. Va sur http://localhost:5000/upload
2. Clique "Trigger Upload"
3. Entre un chemin vidéo
4. Le système :
   - Analyse la vidéo (Narrator)
   - Publie sur les réseaux (Publisher)
   - Notifie par email/Telegram
5. Regarde le résultat dans "Jobs"

### Scénario 2 : Surveillance Automatique (Curator Bot)
1. Lance Curator Bot
2. Drop une vidéo dans `/videos/input`
3. Le bot détecte → envoie au Gateway
4. Le reste est automatique

### Scénario 3 : Monétisation
1. Va sur http://localhost:5000/monetizer
2. Crée un token pour une vidéo
3. QR code généré automatiquement
4. Partage le token ou le QR

---

## 🔧 Configuration Avancée

### IA Personnalisée (Narrator)
Dans `narrator_ai/.env` :
```env
# Option 1 : Ollama (local, gratuit)
AI_PROVIDER=ollama
OLLAMA_MODEL=llama2

# Option 2 : OpenAI (payant, meilleur)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx

# Option 3 : Fallback (gratuit, basique)
AI_PROVIDER=local
```

### Réseaux Sociaux (Publisher)
Dans `publisher_ai/.env` :
```env
# X/Twitter
X_BEARER_USER=ton_token_bearer

# Instagram Business
IG_USER_ID=123456789
IG_ACCESS_TOKEN=EAAG...

# YouTube
YT_CLIENT_SECRETS=./client_secret.json

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_USER=ton@email.com
SMTP_PASS=mot_de_passe_app

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
```

**Tous ces tokens sont OPTIONNELS !**

---

## 🧪 Tests et Débogage

### Tester Manuellement
```bash
# Test Gateway
curl http://localhost:5055/health
curl http://localhost:5055/jobs

# Créer un job test
curl -X POST http://localhost:5055/event \
  -H "Content-Type: application/json" \
  -d '{"event":"test","file":"/tmp/video.mp4","timestamp":"2025-01-01T00:00:00Z"}'

# Créer un token
curl -X POST http://localhost:5060/mint \
  -H "Content-Type: application/json" \
  -d '{"video_id":"vid123","duration_minutes":1440}'
```

### Script de Test Automatique
```bash
./test_system.sh
```

### Logs en Direct (tmux)
```bash
# Attacher à la session
tmux attach -t only

# Navigation :
# Ctrl+B puis N (fenêtre suivante)
# Ctrl+B puis P (fenêtre précédente)
# Ctrl+B puis 0-5 (fenêtre spécifique)
# Ctrl+B puis D (détacher)
```

---

## 📊 Monitoring

### Dashboard Principal
http://localhost:5000
- État des services
- Jobs récents
- Upload rapide

### Sentinel (Avancé)
http://localhost:5059
- Tous les jobs détaillés
- Santé de chaque service
- Statistiques complètes

### APIs Directes
```bash
# Gateway
curl http://localhost:5055/jobs
curl http://localhost:5055/status

# Monetizer
curl http://localhost:5060/tokens
curl http://localhost:5060/stats
```

---

## 🐛 Problèmes Courants

### Port déjà utilisé
```bash
# Voir ce qui utilise le port
lsof -i :5055

# Tuer le processus
kill -9 <PID>

# Ou utilise stop_all.sh
./stop_all.sh
```

### Service ne démarre pas
```bash
# Vérifie les dépendances
cd <service>
pip install -r requirements.txt

# Vérifie le .env
cat .env

# Lance manuellement pour voir les erreurs
python3 <service>.py
```

### Base de données corrompue
```bash
# Supprimer et recréer
rm gateway/gateway.db
rm monetizer_ai/monetizer.db

# Les services vont recréer automatiquement
```

### IA ne fonctionne pas (Narrator)
```bash
# Passe en mode local (basique mais fonctionne)
echo "AI_PROVIDER=local" >> narrator_ai/.env

# Redémarre Narrator
pkill -f narrator_ai.py
cd narrator_ai && python3 narrator_ai.py
```

---

## 📚 Documentation Complète

- [README.md](README.md) - Vue d'ensemble
- [ARCHITECTURE.md](ARCHITECTURE.md) - Détails techniques
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) - Guide Render complet
- [RENDER_CHECKLIST.md](RENDER_CHECKLIST.md) - Checklist déploiement

### Documentation par Service
- [web_interface/README.md](web_interface/README.md)
- [gateway/README.md](gateway/README.md)
- [narrator_ai/README.md](narrator_ai/README.md)
- [publisher_ai/README.md](publisher_ai/README.md)
- [monetizer_ai/README.md](monetizer_ai/README.md)
- [sentinel_dashboard/README.md](sentinel_dashboard/README.md)
- [curator_bot/README.md](curator_bot/README.md)

---

## 💡 Cas d'Usage Réels

### YouTubeur
1. Drop vidéo dans `/videos/input`
2. System analyse et génère titre/description
3. Publie teaser sur X/Instagram
4. Notifie sur Telegram
5. Crée token d'accès premium

### Créateur de Contenu
1. Upload via Web Interface
2. Modifie les métadonnées générées
3. Publie sur plusieurs plateformes
4. Suit les stats en temps réel

### Agence Marketing
1. Upload vidéos clients
2. Planning automatisé via Gateway
3. Publications programmées
4. Analytics centralisé

---

## 🎉 Prochaines Étapes

### Maintenant
- ✅ Tout fonctionne en local
- ✅ Prêt pour Render
- ✅ Interface complète
- ✅ Monétisation intégrée

### Bientôt (Optionnel)
- 🔜 Authentification JWT
- 🔜 Webhooks personnalisés
- 🔜 Analytics avancées
- 🔜 Docker Compose
- 🔜 Support CDN (Bunny, Cloudflare)

---

## 🆘 Support

### Logs
Tous les services affichent leurs logs dans le terminal ou tmux.

### Debugging
```bash
# Activer mode debug dans .env
DEBUG=true

# Relancer le service
```

### Reset Complet
```bash
./stop_all.sh
rm */*.db
./start_all.sh
```

---

**🚀 Tu es prêt ! Commence par `./start_all.sh` et ouvre http://localhost:5000**
