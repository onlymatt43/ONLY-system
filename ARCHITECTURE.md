# ONLY System - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ONLY SYSTEM                                  │
│                   Netflix-Style Modular Platform                     │
└─────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│                   WEB INTERFACE                        │
│  🌐 Dashboard + UI (Port 5000)                        │
│  - Upload vidéos                                       │
│  - Gestion jobs                                        │
│  - Création tokens                                     │
│  - Analytics                                           │
│  - Proxy API (évite CORS)                             │
└─────────────────────┬──────────────────────────────────┘
                      │
           ┌──────────┼──────────┐
           │          │          │
           ▼          ▼          ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Curator Bot  │  │   GATEWAY    │  │ Monetizer AI │
│ 📹 Watch     │  │ 🚦 Queue     │  │ 💰 Tokens    │
│ (optionnel)  │─>│ Port 5055    │<─│ Port 5060    │
│ Port 5054    │  │ - SQLite     │  │ - QR codes   │
└──────────────┘  │ - Idempotent │  │ - HMAC       │
                  │ - Worker     │  └──────────────┘
                  └──────┬───────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │Narrator  │  │Publisher │  │Sentinel  │
      │AI 🧠     │  │AI 📱     │  │📊 Monitor│
      │Port 5056 │  │Port 5058 │  │Port 5059 │
      │- ffprobe │  │- X/IG/YT │  │- Read    │
      │- Ollama  │  │- Email   │  │  Only    │
      └──────────┘  │- Telegram│  └──────────┘
                    └──────────┘
                    
                    Workflow :
                    1. POST /describe → Narrator
                          │  2. POST /build → Builder
                          │  3. POST /notify → Publisher
                          │
                          ▼
              ┌────────────────────────┐
═══════════════════════════════════════════════════════════════════════
                            DATA FLOW
═══════════════════════════════════════════════════════════════════════

SCÉNARIO 1 : Upload via Web Interface
--------------------------------------
1. User → Web Interface : /upload (trigger)
   POST /api/upload → Gateway : /event

2. Job créé (status: queued)
   Gateway → SQLite : INSERT job

3. Analyse métadonnées
   Gateway → Narrator : POST /describe
   Response : {title, description, tags, category}

4. Publication réseaux + notifs
   Gateway → Publisher : POST /notify + POST /social/publish
   Response : {email, telegram, x, instagram, youtube}

5. Job terminé (status: done)
   Gateway → SQLite : UPDATE job SET status='done', link='...'

6. Monitoring temps réel
   Web Interface → Gateway : GET /jobs (via proxy)
   Sentinel → Gateway DB : SELECT * FROM jobs (read-only)


SCÉNARIO 2 : Surveillance Automatique (Curator Bot)
----------------------------------------------------
1. Nouvelle vidéo détectée
   Curator (watchdog) → Gateway : POST /event

2-6. Identique au Scénario 1


SCÉNARIO 3 : Monétisation
--------------------------
1. User → Web Interface : /monetizer
   POST /api/monetizer/mint

2. Token généré
   Monetizer → SQLite : INSERT token
   Response : {token, qr_url, access_url}

3. QR Code créé
   Monetizer : Génère QR code PNG dans /exports

4. Display
   Web Interface : Affiche token + QR code


═══════════════════════════════════════════════════════════════════════
                        COMMUNICATION
═══════════════════════════════════════════════════════════════════════

Protocol: HTTP REST (JSON)
Database: SQLite (local)
Storage: Filesystem (local/NAS)

Tous les blocs sont INDÉPENDANTS :
- Peuvent être redémarrés séparément
- Peuvent tourner sur des machines différentes
- Aucune dépendance bidirectionnelle
- Communication unidirectionnelle uniquement


═══════════════════════════════════════════════════════════════════════
                      EXTERNAL DEPENDENCIES
═══════════════════════════════════════════════════════════════════════

OBLIGATOIRES :
- Python 3.9+
- ffmpeg (ffprobe)

OPTIONNELLES :
- ~~WordPress~~ : remplacé par Web Interface
- Ollama / OpenAI (Narrator AI) : fallback local disponible
- X/Twitter API (Publisher AI) : optionnel
- Instagram Graph API (Publisher AI) : optionnel
- YouTube Data API (Publisher AI) : optionnel
- SMTP server (Publisher AI) : optionnel
- Telegram Bot (Publisher AI) : optionnel

AUCUN service externe n'est requis pour fonctionner !


═══════════════════════════════════════════════════════════════════════
                         DESIGN PRINCIPLES
═══════════════════════════════════════════════════════════════════════

✓ Modulaire     : chaque bloc = micro-service
✓ Autonome      : minimum de dépendances SaaS
✓ Low-cost      : gratuit ou très économique
✓ Automatisé    : IA et bots orchestrent tout
✓ Scalable      : dupliquer/remplacer facilement
✓ Résilient     : retry, idempotence, fallback
✓ Observable    : logs, dashboard, monitoring
✓ Propriétaire  : tu contrôles tout le code/data

```
