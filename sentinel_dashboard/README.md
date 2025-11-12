# 📊 Sentinel Dashboard - Bloc #6

Dashboard de supervision du système ONLY.

## 🎯 Rôle

- Affiche l'état de tous les services en temps réel
- Liste les jobs (queued, running, done, error)
- Ping de santé des micro-services
- Lecture seule de `gateway.db`
- Auto-refresh configurable
- Interface web responsive

## 🚀 Démarrage

```bash
cd sentinel_dashboard
pip install -r requirements.txt
cp .env.example .env
# Éditer .env si besoin
python3 sentinel.py
```

Le dashboard s'ouvre sur **http://localhost:5059**

## ⚙️ Configuration (.env)

```env
PORT=5059
GATEWAY_DB=../gateway/gateway.db
CURATOR_URL=http://localhost:5054/
NARRATOR_URL=http://localhost:5056/
BUILDER_URL=http://localhost:5057/
GATEWAY_URL=http://localhost:5055/
PUBLISHER_URL=http://localhost:5058/
REFRESH_SEC=5
```

## 🔗 API

### GET /
Interface HTML principale (auto-refresh)

### GET /api/services
Status des services en JSON

```bash
curl http://localhost:5059/api/services
```

**Réponse:**
```json
{
  "Curator": {"ok": true, "code": 200},
  "Narrator": {"ok": true, "code": 200},
  "Builder": {"ok": true, "code": 200},
  "Gateway": {"ok": true, "code": 200},
  "Publisher": {"ok": true, "code": 200}
}
```

### GET /api/jobs?limit=100
Liste des jobs en JSON

```bash
curl http://localhost:5059/api/jobs?limit=50
```

### GET /health
Health check

```bash
curl http://localhost:5059/health
```

## 📊 Interface

Le dashboard affiche:

### Services
- État (ONLINE / OFFLINE)
- Code HTTP de réponse
- Erreurs si présentes

### Jobs
- ID du job
- Fichier traité
- Status (queued / running / done / error)
- Lien du post publié
- Timestamp de dernière mise à jour

## 🔒 Sécurité

- Lecture seule de la base de données (`mode=ro`)
- Aucune écriture possible
- Aucune modification des jobs
- Simple observateur passif

## 🔧 Indépendance

- Bloc complètement séparé
- Peut être arrêté sans impact sur les autres
- Peut tourner sur une autre machine
- Pas de dépendance forte
- Communication HTTP uniquement

## 🎨 Design

- Interface sombre (dark mode)
- Auto-refresh toutes les 5s (configurable)
- Responsive
- Minimaliste
- Zéro JavaScript externe
