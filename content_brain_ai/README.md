# Content Brain AI

Service d'analyse vidéo intelligent pour marketing automatisé.

## 🎯 Fonctionnalités

### Video Analyzer
- **Analyse métadonnées** : Durée, résolution, qualité thumbnail
- **Content typing** : Tutorial, review, vlog, teaser, entertainment
- **Energy detection** : Low, medium, high
- **Key timestamps** : Hook, climax, cliffhanger
- **Preview segments** : Segments optimaux par plateforme
- **Marketing scores** : Engagement (0-10), viral potential (0-10)
- **Platform fit** : Score par plateforme (Twitter, IG, FB, LinkedIn, Bluesky)
- **Hooks generation** : 3-5 titres accrocheurs suggérés
- **CTA strategy** : Timing et type optimal

### Batch Analyzer
- Analyse multiple vidéos
- Top performers par métrique
- Stats agrégées catalogue

## 🚀 Installation

```bash
cd content_brain_ai
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec tes configs
```

## ⚙️ Configuration

```env
PORT=5070
CURATOR_URL=http://localhost:5061
```

## 🎬 Utilisation

### Démarrer le service

```bash
python content_brain.py
```

### API Endpoints

#### 1. Analyser une vidéo
```bash
POST /analyze/<video_id>

# Exemple
curl -X POST http://localhost:5070/analyze/123

# Response
{
  "ok": true,
  "video_id": "123",
  "insights": {
    "duration_seconds": 180,
    "engagement_score": 7.5,
    "viral_potential": 6.2,
    "platform_fit": {
      "twitter": 8.5,
      "instagram": 7.8,
      "facebook": 6.3,
      "linkedin": 5.2,
      "bluesky": 7.9
    },
    "suggested_hooks": [
      "🔥 Cette technique va te choquer",
      "💡 La méthode que PERSONNE ne connaît",
      ...
    ],
    "best_preview_segments": [
      {
        "start": 0,
        "end": 30,
        "duration": 30,
        "reason": "strong_hook",
        "platforms": ["twitter", "instagram"]
      }
    ]
  }
}
```

#### 2. Analyse batch
```bash
POST /analyze/batch
Content-Type: application/json

{
  "library": "public",  # public, private, all
  "limit": 10
}

# Exemple
curl -X POST http://localhost:5070/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{"library":"public","limit":5}'
```

#### 3. Top performers
```bash
GET /top-performers?metric=engagement&limit=10&library=all

# Métriques disponibles:
# - engagement
# - viral_potential
# - twitter, instagram, facebook, linkedin, bluesky

# Exemple
curl "http://localhost:5070/top-performers?metric=viral_potential&limit=5"
```

#### 4. Preview optimal pour plateforme
```bash
GET /preview/<video_id>/<platform>

# Exemple
curl http://localhost:5070/preview/123/twitter

# Response
{
  "ok": true,
  "video_id": "123",
  "platform": "twitter",
  "preview_segment": {
    "start": 0,
    "end": 30,
    "duration": 30,
    "reason": "strong_hook",
    "platforms": ["twitter", "instagram", "linkedin"],
    "description": "Début accrocheur avec hook fort"
  },
  "platform_fit_score": 8.5
}
```

#### 5. Hooks suggérés
```bash
GET /hooks/<video_id>

# Exemple
curl http://localhost:5070/hooks/123

# Response
{
  "ok": true,
  "video_id": "123",
  "hooks": [
    "🔥 Cette technique va te choquer",
    "💡 La méthode que PERSONNE ne connaît",
    "⚡ Résultats en 5 minutes",
    "😱 J'ai testé - CHOQUANT",
    "🎯 Comment faire comme un pro"
  ],
  "engagement_score": 7.5,
  "viral_potential": 6.2
}
```

#### 6. Stats globales
```bash
GET /stats?library=all

# Exemple
curl "http://localhost:5070/stats?library=public"

# Response
{
  "ok": true,
  "library": "public",
  "total_videos": 14,
  "averages": {
    "engagement_score": 6.8,
    "viral_potential": 5.9,
    "platform_fit": {
      "twitter": 7.2,
      "instagram": 6.9,
      "facebook": 6.1,
      "linkedin": 5.3,
      "bluesky": 7.0
    }
  },
  "content_types": {
    "tutorial": 5,
    "entertainment": 6,
    "vlog": 2,
    "teaser": 1
  },
  "energy_levels": {
    "high": 8,
    "medium": 4,
    "low": 2
  }
}
```

## 📊 Algorithmes

### Engagement Score (0-10)
- **Durée optimale** : 60-300s (+2.0)
- **High energy** : +1.5
- **Bonne thumbnail** : +1.0
- **Titre engageant** : +0.5

### Viral Potential (0-10)
- **Courte vidéo** : <60s (+3.0), <120s (+1.5)
- **High energy** : +2.0
- **Type viral** : teaser, entertainment (+1.0)

### Platform Fit (0-10)
Basé sur:
- Durée idéale plateforme
- Energy level préféré
- Format (vertical/horizontal/carré)

**Durées idéales** :
- Twitter: 30s
- Instagram: 60s
- Facebook: 90s
- LinkedIn: 45s
- Bluesky: 45s

## 🧠 Intelligence

### Content Type Detection
Détecte automatiquement:
- **Tutorial** : "how to", "guide", "learn"
- **Review** : "review", "test", "comparison"
- **Vlog** : "vlog", "day in", "behind"
- **Teaser** : <60s
- **Entertainment** : default

### Energy Level Detection
Analyse:
- Durée (court = high energy)
- Emojis dans titre
- Majuscules
- Points d'exclamation

### Preview Segments Generation
4 types de segments:
1. **Strong Hook** (0-30s) : Accroche attention
2. **Action Peak** (climax ±15s) : Moment intense
3. **Cliffhanger** (30s finaux) : Donne envie suite
4. **Extended Preview** (0-90s) : Contexte complet

### Hooks Generation
Templates par type:
- **Tutorial** : "Comment faire X", "Technique secrète"
- **Review** : "J'ai testé X", "La vérité sur X"
- **Teaser** : "Tu n'es PAS prêt", "Attends de voir"
- **Entertainment** : "C'est INSANE", "Meilleur moment"

## 🔗 Intégration

### Avec Curator Bot
Content Brain récupère données vidéos via Curator API:
```python
GET http://localhost:5061/videos/<id>
```

### Avec Content Scheduler (à venir)
Scheduler utilisera insights pour:
- Choisir meilleur timing post
- Adapter contenu par plateforme
- Générer hooks optimisés

### Avec Style AI (à venir)
Style AI utilisera hooks suggérés et les adaptera à TON style.

## 📈 Prochaines Évolutions

### Phase 1 (actuel)
- [x] Analyse métadonnées basique
- [x] Scoring engagement/viral
- [x] Platform fit
- [x] Hooks génération
- [x] Preview segments

### Phase 2
- [ ] Analyse thumbnail avec vision AI
- [ ] Détection objets/scènes dans vidéo
- [ ] Transcription audio pour meilleurs hooks
- [ ] Sentiment analysis

### Phase 3
- [ ] ML model pour prédictions engagement
- [ ] A/B testing hooks automatique
- [ ] Recommendations personnalisées
- [ ] Auto-optimization basée sur performance

## 🧪 Testing

```bash
# Test avec vidéo locale (requiert Curator running)
python video_analyzer.py

# Test API
python content_brain.py

# Dans autre terminal
curl http://localhost:5070/
curl -X POST http://localhost:5070/analyze/1
curl "http://localhost:5070/stats"
```

## 🐛 Debug

Si erreurs:
1. **Curator non accessible** : Vérifie que Curator tourne sur port 5061
2. **Vidéo not found** : Vérifie que vidéo existe dans Curator DB
3. **Import errors** : `pip install -r requirements.txt`

## 📝 Notes

- Tous les scores sont 0-10
- Durées en secondes
- Timestamps relatifs au début vidéo (0s)
- Platform fit calculé dynamiquement
- Hooks peuvent être customizés après génération

---

**Content Brain AI - La fondation du marketing automatisé ONLY** 🧠✨
