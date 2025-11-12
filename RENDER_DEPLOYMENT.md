# 🌐 ONLY - Déploiement sur Render

Guide complet pour déployer ONLY sur Render.com

## 📋 Architecture sur Render

Chaque bloc sera un **Web Service** séparé sur Render :

1. **web-interface** (port 5000) - Interface utilisateur
2. **gateway** (port 5055) - Orchestrateur
3. **narrator-ai** (port 5056) - Analyse vidéo
4. **publisher-ai** (port 5058) - Publication réseaux
5. **monetizer-ai** (port 5060) - Gestion tokens

**Note:** Builder Bot est retiré car on n'utilise plus WordPress.

## 🚀 Étapes de déploiement

### 1. Préparer le repo Git

```bash
cd /Users/mathieucourchesne/Sources/ONLY

# Initialiser git si pas déjà fait
git init
git add .
git commit -m "Initial commit - ONLY system"

# Créer un repo sur GitHub et pusher
git remote add origin https://github.com/TON_USERNAME/ONLY.git
git push -u origin main
```

### 2. Créer les services sur Render

Va sur [render.com](https://render.com) et crée **5 Web Services** :

#### Service 1: Web Interface
- **Name:** `only-web`
- **Environment:** Python 3
- **Build Command:** `cd web_interface && pip install -r requirements.txt`
- **Start Command:** `cd web_interface && uvicorn web_interface:app --host 0.0.0.0 --port $PORT`
- **Plan:** Free (ou payant si besoin)

**Variables d'environnement:**
```
PORT=5000
GATEWAY_URL=https://only-gateway.onrender.com
NARRATOR_URL=https://only-narrator.onrender.com
PUBLISHER_URL=https://only-publisher.onrender.com
MONETIZER_URL=https://only-monetizer.onrender.com
```

#### Service 2: Gateway
- **Name:** `only-gateway`
- **Build Command:** `cd gateway && pip install -r requirements.txt`
- **Start Command:** `cd gateway && python gateway.py`

**Variables d'environnement:**
```
PORT=5055
NARRATOR_URL=https://only-narrator.onrender.com/describe
PUBLISHER_URL=https://only-publisher.onrender.com/notify
DB_PATH=./gateway.db
WORKER_INTERVAL_SEC=5
```

#### Service 3: Narrator AI
- **Name:** `only-narrator`
- **Build Command:** `cd narrator_ai && pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`
- **Start Command:** `cd narrator_ai && python narrator_ai.py`

**Variables d'environnement:**
```
PORT=5056
AI_PROVIDER=local
```

#### Service 4: Publisher AI
- **Name:** `only-publisher`
- **Build Command:** `cd publisher_ai && pip install -r requirements.txt`
- **Start Command:** `cd publisher_ai && python publisher_ai.py`

**Variables d'environnement:**
```
PORT=5058
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ton@email.com
SMTP_PASS=motdepasse
# Ajoute tes tokens X, IG, YouTube ici
```

#### Service 5: Monetizer AI
- **Name:** `only-monetizer`
- **Build Command:** `cd monetizer_ai && pip install -r requirements.txt`
- **Start Command:** `cd monetizer_ai && python monetizer_ai.py`

**Variables d'environnement:**
```
PORT=5060
DB_PATH=./monetizer.db
BASE_URL=https://only-monetizer.onrender.com
SECRET_KEY=ton-secret-super-long-et-unique
CODE_PREFIX=OM43
DEFAULT_DURATION_MIN=1440
```

## 🗄️ Gestion des bases de données

### Option 1: SQLite avec Render Disks (Recommandé)

Pour chaque service qui utilise SQLite (Gateway, Monetizer), ajoute un **Disk** sur Render :

1. Dans les settings du service
2. **Add Disk**
3. **Name:** `data`
4. **Mount Path:** `/data`
5. **Size:** 1GB (gratuit)

Puis modifie les variables d'environnement :
```
DB_PATH=/data/gateway.db
DB_PATH=/data/monetizer.db
```

### Option 2: PostgreSQL (Production)

Pour une solution production, utilise PostgreSQL :

1. Crée une **PostgreSQL Database** sur Render
2. Récupère l'URL de connexion
3. Modifie les services pour utiliser PostgreSQL au lieu de SQLite

## 📡 CORS et Communication entre services

Tous les services communiquent via leurs URLs publiques Render :
- `https://only-gateway.onrender.com`
- `https://only-narrator.onrender.com`
- etc.

Pas besoin de configuration CORS spéciale car tout est backend.

## 🔐 Secrets et Variables

**NE JAMAIS** commiter les `.env` avec des vrais secrets !

Sur Render, toutes les variables sensibles sont dans les **Environment Variables** de chaque service.

## 🧪 Tester le déploiement

Une fois tous les services déployés :

1. Va sur `https://only-web.onrender.com`
2. Le dashboard devrait afficher l'état de tous les services
3. Test upload une vidéo
4. Vérifie que le job apparaît dans "Jobs"

## ⚡ Optimisations

### Keep services awake (Free tier)

Les services gratuits sur Render "dorment" après inactivité. Solutions :

1. **UptimeRobot** : ping tes services toutes les 5 min
2. **Cron-job.org** : même principe
3. **Upgrade to paid** : $7/mois par service pour qu'ils restent actifs

### Health checks

Chaque service a un endpoint `/health` que Render peut ping.

## 📊 Monitoring

- **Logs:** Voir les logs de chaque service dans le dashboard Render
- **Metrics:** Render fournit CPU, RAM, requêtes
- **Sentinel:** Ton dashboard ONLY affiche l'état en temps réel

## 🚨 Troubleshooting

### Service ne démarre pas
- Vérifie les logs sur Render
- Assure-toi que toutes les variables d'environnement sont définies
- Vérifie que les URLs des autres services sont correctes

### Base de données perdue
- Utilise Render Disks (persistent storage)
- Ou PostgreSQL pour production

### Services trop lents
- Free tier = cold starts
- Upgrade vers Starter ($7/mois) pour performances

## 💰 Coûts estimés

### Free Tier (possible mais limité)
- 5 services × 750h/mois gratuit = OK si peu utilisé
- Limitation: services "dorment" après 15min d'inactivité

### Starter Plan ($35/mois total)
- 5 services × $7/mois = $35/mois
- Services toujours actifs
- Meilleures performances

### Production ($100+/mois)
- PostgreSQL géré: $7/mois
- Services Standard: $25/mois chacun
- CDN pour vidéos (Bunny, Cloudflare R2)

---

**Tu as maintenant tout ce qu'il faut pour déployer ONLY sur Render sans WordPress !** 🚀
