# ✅ Checklist Déploiement Render

## 📋 Avant de commencer

- [ ] Compte GitHub créé
- [ ] Compte Render.com créé (gratuit)
- [ ] Tous les services locaux testés et fonctionnels

## 🔧 Étape 1 : Préparer le code

```bash
cd /Users/mathieucourchesne/Sources/ONLY

# Créer .gitignore si nécessaire
cat > .gitignore << 'EOF'
*.pyc
__pycache__/
.env
*.db
*.log
.DS_Store
exports/
videos/
EOF

# Initialiser git
git init
git add .
git commit -m "Initial commit - ONLY system ready for Render"
```

## 🚀 Étape 2 : Pusher sur GitHub

```bash
# Créer un nouveau repo sur https://github.com/new
# Nom suggéré : ONLY-system

# Lier et pusher
git remote add origin https://github.com/TON_USERNAME/ONLY-system.git
git branch -M main
git push -u origin main
```

## 🌐 Étape 3 : Créer les services sur Render

Va sur https://dashboard.render.com et crée **5 Web Services** :

### Service 1/5 : Web Interface ⭐ (PUBLIC)

1. **New Web Service**
2. Connect ton repo GitHub
3. Configuration :
   - **Name:** `only-web`
   - **Root Directory:** `web_interface`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn web_interface:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (ou Starter $7/mois)

4. **Environment Variables** :
   ```
   GATEWAY_URL = https://only-gateway.onrender.com
   NARRATOR_URL = https://only-narrator.onrender.com
   PUBLISHER_URL = https://only-publisher.onrender.com
   MONETIZER_URL = https://only-monetizer.onrender.com
   ```
**NOTE:** If you enable Bunny Token Authentication for your private library (389178), add this env var to `only-public`:

```
BUNNY_SECURITY_KEY=your-bunny-security-key
```

5. Deploy

### Service 2/5 : Gateway 🔧 (PRIVÉ)

1. **New Web Service**
2. Configuration :
   - **Name:** `only-gateway`
   - **Root Directory:** `gateway`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python gateway.py`

3. **Environment Variables** :
   ```
   PORT = 5055
   NARRATOR_URL = https://only-narrator.onrender.com/describe
   PUBLISHER_URL = https://only-publisher.onrender.com/notify
   DB_PATH = /data/gateway.db
   WORKER_INTERVAL_SEC = 5
   ```

4. **Disk Storage** (important !) :
   - Add Disk
   - Name: `gateway-data`
   - Mount Path: `/data`
   - Size: 1 GB

5. Deploy

### Service 3/5 : Narrator AI 🎬 (PRIVÉ)

1. **New Web Service**
2. Configuration :
   - **Name:** `only-narrator`
   - **Root Directory:** `narrator_ai`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python narrator_ai.py`

3. **Environment Variables** :
   ```
   PORT = 5056
   AI_PROVIDER = local
   ```

4. Deploy

### Service 4/5 : Publisher AI 📱 (PRIVÉ)

1. **New Web Service**
2. Configuration :
   - **Name:** `only-publisher`
   - **Root Directory:** `publisher_ai`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python publisher_ai.py`

3. **Environment Variables** (tous optionnels) :
   ```
   PORT = 5058
   SMTP_SERVER = smtp.gmail.com
   SMTP_PORT = 587
   SMTP_USER = ton@email.com
   SMTP_PASS = xxxxx
   
   # Ajoute tes tokens X, IG, YouTube si tu veux
   ```

4. Deploy

### Service 5/5 : Monetizer AI 💰 (PRIVÉ)

1. **New Web Service**
2. Configuration :
   - **Name:** `only-monetizer`
   - **Root Directory:** `monetizer_ai`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python monetizer_ai.py`

3. **Environment Variables** :
   ```
   PORT = 5060
   DB_PATH = /data/monetizer.db
   BASE_URL = https://only-monetizer.onrender.com
   SECRET_KEY = [génère une clé aléatoire longue]
   CODE_PREFIX = OM43
   DEFAULT_DURATION_MIN = 1440
   ```

4. **Disk Storage** :
   - Add Disk
   - Name: `monetizer-data`
   - Mount Path: `/data`
   - Size: 1 GB

5. Deploy

## ⏱️ Étape 4 : Attendre le déploiement

- Chaque service prend **5-10 minutes** pour le premier déploiement
- Regarde les logs en temps réel pour chaque service
- Vérifie qu'il n'y a pas d'erreurs critiques

## ✅ Étape 5 : Tester

1. Va sur ton URL Web Interface : **https://only-web.onrender.com**

2. Le dashboard devrait afficher :
   - ✅ Gateway : OK
   - ✅ Narrator : OK
   - ✅ Publisher : OK
   - ✅ Monetizer : OK

3. Test complet :
   - Upload → Créer un job test
   - Jobs → Voir le job apparaître
   - Monetizer → Créer un token
   - Analytics → Voir les stats

## 🐛 Troubleshooting

### Service ne démarre pas
```bash
# Vérifie les logs dans Render Dashboard
# Causes communes :
- Variables d'environnement manquantes
- URLs incorrectes
- Problème de dépendances Python
```

### Cold starts (Free tier)
Les services gratuits "dorment" après 15min d'inactivité.
Solutions :
- Utilise UptimeRobot pour ping toutes les 5min
- Upgrade vers Starter ($7/mois) pour rester actif

### Base de données perdue
- Vérifie que les Disks sont bien montés sur `/data`
- Change `DB_PATH` vers `/data/xxx.db`

## 💰 Coûts

### Option 1 : Gratuit (avec limitations)
- 5 services × 750h/mois = OK
- ⚠️ Services dorment après 15min
- ⚠️ Cold start = 30-60 secondes

**Total : 0$/mois**

### Option 2 : Production (recommandé)
- 5 services × $7/mois = $35/mois
- ✅ Services toujours actifs
- ✅ Pas de cold start
- ✅ Plus de RAM/CPU

**Total : $35/mois**

## 🎉 Terminé !

Tu as maintenant ONLY déployé sur Render sans WordPress !

**URL publique :** https://only-web.onrender.com

**Prochaines étapes :**
- Configure tes tokens réseaux sociaux dans Publisher
- Ajoute un domaine custom (optionnel)
- Active les notifications (email/Telegram)
- Teste le workflow complet avec une vraie vidéo
