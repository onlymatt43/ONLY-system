# Déploiement Sentinel Dashboard sur Render

## Informations du service

**Nom**: `only-sentinel`  
**Root Directory**: `sentinel_dashboard`  
**Build Command**: `pip install -r requirements.txt`  
**Start Command**: `python sentinel.py`

## Variables d'environnement requises

```bash
PORT=10000
GATEWAY_URL=https://only-gateway.onrender.com
CURATOR_URL=https://only-curator.onrender.com
NARRATOR_URL=https://only-narrator.onrender.com
BUILDER_URL=https://only-builder.onrender.com
PUBLISHER_URL=https://only-publisher.onrender.com
REFRESH_SEC=5
```

## Étapes de déploiement

1. **Créer nouveau Web Service sur Render**
   - Se connecter à Render.com
   - Cliquer "New +" → "Web Service"
   - Connecter le repo GitHub: `onlymatt43/ONLY-system`
   - Branch: `main`

2. **Configurer le service**
   - Name: `only-sentinel`
   - Region: `Oregon (US West)`
   - Root Directory: `sentinel_dashboard`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python sentinel.py`
   - Instance Type: `Free`

3. **Ajouter les 7 variables d'environnement**
   - Copier-coller depuis la section ci-dessus
   - Vérifier les URLs des autres services

4. **Déployer**
   - Cliquer "Create Web Service"
   - Attendre 3-5 minutes pour le build

## Test après déploiement

```bash
# Health check
curl https://only-sentinel.onrender.com/health

# API jobs (via Gateway)
curl https://only-sentinel.onrender.com/api/jobs

# API services status
curl https://only-sentinel.onrender.com/api/services

# Dashboard HTML
curl https://only-sentinel.onrender.com/
```

## Architecture

Sentinel Dashboard:
- **Lit les jobs via Gateway API** (`/jobs`) au lieu de SQLite direct
- **Ping tous les services** pour vérifier leur statut
- **Auto-refresh** toutes les 5 secondes
- **Dashboard HTML** avec Jinja2 templates

Dépendances entre services:
- Sentinel → Gateway (lecture des jobs)
- Sentinel → Tous les services (health checks)

## Notes importantes

✅ **Plus de dépendance SQLite** - Sentinel utilise maintenant l'API Gateway
✅ **Compatible Render** - Pas de fichiers partagés nécessaires
✅ **Monitoring temps réel** - Statut de tous les services en un coup d'œil
