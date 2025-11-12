# 🌐 Web Interface - Bloc #7

Interface web complète pour gérer le système ONLY.

## 🎯 Rôle

- Dashboard centralisé pour tous les services
- Upload et gestion de vidéos
- Visualisation des jobs en temps réel
- Gestion des tokens de monétisation
- Analytics et statistiques
- **Remplace WordPress** comme interface utilisateur

## 🚀 Démarrage

```bash
cd web_interface
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec les URLs des services
python3 web_interface.py
```

Le service démarre sur **http://localhost:5000**

## ⚙️ Configuration (.env)

```env
PORT=5000
GATEWAY_URL=http://localhost:5055
NARRATOR_URL=http://localhost:5056
BUILDER_URL=http://localhost:5057
PUBLISHER_URL=http://localhost:5058
SENTINEL_URL=http://localhost:5059
MONETIZER_URL=http://localhost:5060
```

Pour Render (production) :
```env
GATEWAY_URL=https://only-gateway.onrender.com
NARRATOR_URL=https://only-narrator.onrender.com
PUBLISHER_URL=https://only-publisher.onrender.com
MONETIZER_URL=https://only-monetizer.onrender.com
```

## 🔗 Pages

### Dashboard (/)
- État de tous les services en temps réel
- Jobs récents
- Actions rapides

### Upload (/upload)
- Formulaire d'upload de vidéos
- Suivi du traitement en temps réel

### Jobs (/jobs)
- Liste complète des jobs
- Filtrage et recherche
- Liens vers les contenus publiés

### Monetizer (/monetizer)
- Création de tokens d'accès
- Gestion des tokens existants
- QR codes automatiques

### Analytics (/analytics)
- Statistiques globales
- Graphiques de performance

## 🎨 Design

- Interface dark mode moderne
- Responsive (mobile-friendly)
- Auto-refresh des données
- Pas de dépendance externe (CSS/JS vanilla)

## 🔧 API Proxy

Le web interface sert de proxy pour éviter les problèmes CORS :

- `GET /api/status` - État des services
- `GET /api/jobs` - Liste des jobs
- `POST /api/upload` - Déclencher un traitement
- `POST /api/monetizer/mint` - Créer un token
- `GET /api/monetizer/tokens` - Liste des tokens

## 🌐 Déploiement sur Render

```bash
# Build Command
cd web_interface && pip install -r requirements.txt

# Start Command
cd web_interface && uvicorn web_interface:app --host 0.0.0.0 --port $PORT
```

## 🔒 Sécurité

Pour production :
- Ajouter authentification (JWT)
- Rate limiting
- HTTPS obligatoire
- Variables d'environnement pour tous les secrets

## 📱 Mobile

L'interface est responsive et fonctionne sur mobile, tablette et desktop.

## ✅ Avantages vs WordPress

- ✓ Pas de plugin à gérer
- ✓ Interface sur mesure
- ✓ Pas de base de données complexe
- ✓ Déploiement simple
- ✓ Performance optimale
- ✓ Contrôle total du code
