# 🚦 Gateway - Bloc #4

Orchestrateur central du système ONLY.

## 🎯 Rôle

- Reçoit les événements du Curator Bot
- Orchestre le flux : Curator → Narrator → Builder → Publisher
- File d'attente avec SQLite
- Idempotence (ne retraite pas les fichiers déjà traités)
- Retry automatique sur erreurs réseau
- Worker asynchrone

## 🚀 Démarrage

```bash
cd gateway
pip install -r requirements.txt
cp .env.example .env
# Éditer .env si besoin
python3 gateway.py
```

Le service démarre sur **http://localhost:5055**

## ⚙️ Configuration (.env)

```env
PORT=5055
NARRATOR_URL=http://localhost:5056/describe
BUILDER_URL=http://localhost:5057/build
PUBLISHER_URL=http://localhost:5058/notify
WORKER_INTERVAL_SEC=2
```

## 🔗 API

### GET /
Status du service

### POST /event
Reçoit un événement (généralement du Curator)

```bash
curl -X POST http://localhost:5055/event \
  -H "Content-Type: application/json" \
  -d '{
    "event": "new_video",
    "file": "/videos/input/scene1.mov",
    "timestamp": "2025-11-12T01:23:45Z"
  }'
```

**Réponse:**
```json
{
  "ok": true,
  "enqueued_job_id": 42
}
```

### GET /jobs
Liste les jobs (50 derniers par défaut)

```bash
curl http://localhost:5055/jobs?limit=100
```

### GET /jobs/{job_id}
Détails d'un job spécifique

```bash
curl http://localhost:5055/jobs/42
```

## 📊 Base de données

SQLite : `gateway.db`

**Table jobs:**
- `id` : identifiant unique
- `file` : chemin du fichier
- `status` : queued | running | done | error
- `narrator_json` : métadonnées générées
- `post_id` : ID du post WordPress
- `link` : URL du post publié
- `last_error` : message d'erreur si échec
- `created_at` / `updated_at` : timestamps

## 🔄 Workflow

1. **Curator** envoie `POST /event` avec un nouveau fichier
2. **Gateway** crée un job en status `queued`
3. **Worker** prend le job et:
   - Appelle **Narrator** → génère métadonnées
   - Appelle **Builder** → crée post WordPress
   - Appelle **Publisher** → notifie + publie sur réseaux
4. Job passe en status `done` avec `post_id` et `link`

## 🔧 Indépendance

- SQLite local (pas de serveur DB externe)
- Idempotence : même fichier traité une seule fois
- Retry réseau automatique (3 tentatives)
- Queue inspectable en temps réel
- Tous les blocs restent remplaçables

## 🧠 Coeur du système

Le Gateway est le **hub central** :
- Les autres services sont indépendants
- Chacun peut être redémarré sans affecter les autres
- Communication 100% HTTP/JSON
