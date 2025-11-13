# Style Learner AI - Documentation

Capture et réplique ton style d'écriture unique pour générer du contenu authentique.

## 🎯 Objectif

Le Style Learner analyse tes posts existants (Twitter, Instagram, etc.) pour apprendre:
- Ton **vocabulary level** (casual, professional, expert)
- Ton **tone** (friendly, direct, humorous, energetic)
- Ton **energy level** et **formality** (scores 0-10)
- Tes **catchphrases** et mots favoris
- Ton usage d'**emojis** (fréquence, placement, favoris)
- Ta **structure de posts** (hook, body, CTA, links)
- Tes **types de hooks** (question, emoji_start, caps, exclamation)

Ensuite, il génère des posts qui "sonnent exactement comme toi" basés sur le contenu vidéo à promouvoir.

---

## 📊 StyleProfile - 16 Champs

```python
@dataclass
class StyleProfile:
    # Linguistic patterns
    vocabulary_level: str          # casual | professional | expert
    sentence_length: str           # short | medium | long
    punctuation_style: str         # minimal | standard | expressive
    
    # Tone & voice
    tone: List[str]                # [friendly, direct, humorous, energetic]
    formality: int                 # 0-10 (0=très casual, 10=très formel)
    energy: int                    # 0-10 (0=calme, 10=hyper énergique)
    
    # Signature expressions
    catchphrases: List[str]        # ["OK LES GARS", "C'EST INSANE"]
    common_words: List[str]        # Top 10 mots utilisés
    
    # Emojis
    emoji_frequency: str           # none | low | medium | high
    favorite_emojis: List[str]     # Top 10 emojis
    emoji_placement: str           # start | end | inline | mixed
    
    # Post structure
    typical_structure: List[str]   # [hook, body, cta, link]
    avg_post_length: int           # caractères
    uses_hashtags: bool
    hashtag_count_avg: int
    
    # Hooks
    hook_types: List[str]          # Types de hooks détectés
    hook_examples: List[str]       # Exemples concrets
    
    # Metadata
    analyzed_posts_count: int
    confidence_score: float        # 0-1
```

---

## 🔧 API Endpoints

### 1. Training - `/style/train`

**POST** - Entraîne le Style Learner avec tes posts existants.

```bash
curl -X POST http://localhost:5070/style/train \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [
      {
        "text": "🔥 OK LES GARS\n\nJ'\''ai découvert un truc INSANE...",
        "platform": "twitter"
      },
      {
        "text": "💡 Cette technique va te choquer...",
        "platform": "instagram"
      }
    ]
  }'
```

**Response:**
```json
{
  "ok": true,
  "message": "Training posts added successfully",
  "total_training_posts": 15
}
```

**Recommandation:** Minimum 5 posts, optimal 20+, excellent 50+.

---

### 2. Analyze - `/style/analyze`

**POST** - Analyse tous les posts training et génère StyleProfile.

```bash
curl -X POST http://localhost:5070/style/analyze
```

**Response:**
```json
{
  "ok": true,
  "style_profile": {
    "vocabulary_level": "casual",
    "sentence_length": "medium",
    "punctuation_style": "expressive",
    "tone": ["friendly", "direct", "energetic"],
    "formality": 2,
    "energy": 8,
    "catchphrases": ["OK LES GARS", "C'EST INSANE"],
    "common_words": ["regarde", "check", "vidéo", "insane"],
    "emoji_frequency": "high",
    "favorite_emojis": ["🔥", "👇", "💡", "👀", "😱"],
    "emoji_placement": "start",
    "typical_structure": ["hook", "body", "cta", "link"],
    "avg_post_length": 180,
    "uses_hashtags": true,
    "hashtag_count_avg": 2.5,
    "hook_types": ["emoji_start", "exclamation"],
    "hook_examples": ["🔥 OK LES GARS", "💡 Cette technique va te choquer"],
    "analyzed_posts_count": 15,
    "confidence_score": 0.75
  },
  "message": "Style analyzed from 15 posts"
}
```

---

### 3. Get Profile - `/style/profile`

**GET** - Récupère StyleProfile actuel (après training + analyze).

```bash
curl -X GET http://localhost:5070/style/profile
```

---

### 4. Generate Post - `/style/generate`

**POST** - Génère un post dans TON style pour une vidéo spécifique.

```bash
curl -X POST http://localhost:5070/style/generate \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "135",
    "platform": "twitter"
  }'
```

**Response:**
```json
{
  "ok": true,
  "video_id": "135",
  "platform": "twitter",
  "generated_post": "🔥 OK LES GARS\n\nJ'ai passé des heures sur cette vidéo insane...\n\nTu vas kiffer 💯\n\n🔗 Vidéo complète ci-dessous\n\n#tutorial #insane",
  "style_match_score": 0.85,
  "video_insights": {
    "engagement_score": 7.5,
    "viral_potential": 6.2,
    "content_type": "tutorial"
  }
}
```

**Processus de génération:**
1. Récupère VideoInsights (engagement, hooks suggérés, content_type)
2. Adapte hooks suggérés à TON style
3. Génère body avec ton energy level
4. Ajoute emojis selon ton placement habituel
5. Ajoute CTA selon ta structure
6. Ajoute hashtags selon ton avg
7. Valide style match (0-1)

---

### 5. Validate Style - `/style/validate`

**POST** - Valide si un post match ton style (score 0-1).

```bash
curl -X POST http://localhost:5070/style/validate \
  -H "Content-Type: application/json" \
  -d '{
    "post_text": "🔥 Check cette vidéo insane les gars! Tu vas kiffer 💯"
  }'
```

**Response:**
```json
{
  "ok": true,
  "post_text": "🔥 Check cette vidéo insane les gars! Tu vas kiffer 💯",
  "style_match_score": 0.92,
  "interpretation": "Excellent - sounds exactly like you"
}
```

**Interprétations:**
- **0.8+**: Excellent - sounds exactly like you
- **0.6-0.8**: Good - minor adjustments needed
- **<0.6**: Poor - doesn't match your style

**5 checks effectués:**
1. **Emoji usage** - Fréquence match ton style?
2. **Post length** - Dans ±30% de ton avg?
3. **Energy level** - Caps/exclamations match ton energy?
4. **Vocabulary** - Utilise tes common words?
5. **Catchphrases** - Contient tes expressions signature?

---

## 🧪 Algorithmes d'Analyse

### Vocabulary Analysis

```python
def _analyze_vocabulary(posts):
    # 1. Mots communs (exclude stop words)
    # 2. Catchphrases (2-4 word patterns en CAPS ou avec !!)
    # 3. Complexity ratio (mots >8 chars)
    #    >15% = expert
    #    >8% = professional
    #    <8% = casual
    # 4. Sentence length (split by .!?)
    #    <8 words = short
    #    8-15 words = medium
    #    >15 words = long
    # 5. Punctuation style (! et ? per 1000 chars)
    #    >15/1000 = expressive
    #    5-15/1000 = standard
    #    <5/1000 = minimal
```

### Tone Analysis

```python
def _analyze_tone(posts):
    # Friendly: "merci", "cool", "super", "génial"
    # Direct: "regarde", "check", "écoute", "fais"
    # Humorous: "😂", "lol", "mdr", "haha"
    # Energetic: "insane", "fou", "incroyable", "🔥"
    
    # Formality score (baseline 5):
    #   +3 if formal words ("veuillez", "cordialement")
    #   -3 if casual words ("yo", "mec", "bro")
    
    # Energy score (baseline 5):
    #   +2 if caps ratio >10%
    #   +2 if exclamation ratio >1.5%
    #   +1 if energy emojis (🔥⚡💥🚀)
```

### Emoji Analysis

```python
def _analyze_emojis(posts):
    # Extract all emojis (Unicode ranges)
    # Frequency:
    #   ≥3 emojis/post = high
    #   ≥1 emoji/post = medium
    #   <1 emoji/post = low
    
    # Placement:
    #   Check first 20 chars → start
    #   Check last 20 chars → end
    #   Check middle → inline
    #   Mix → mixed
    
    # Favorites: Top 10 most used
```

### Hook Detection

```python
hook_patterns = {
    "question": r"^\?|^Comment |^Pourquoi ",
    "emoji_start": r"^[😀-🙏💀-🙏🚀-🛸🔥⚡💎💯✨👀🎯]",
    "caps_statement": r"^[A-Z\s]{10,}",
    "exclamation": r"^[^\n]+!",
    "number": r"^\d+",
    "direct_address": r"^(OK|YO|HEY|LES GARS|REGARDE)"
}
```

---

## 🎨 Post Generation Process

```python
def generate_post(video_insights, platform):
    """
    1. HOOK
       - Récupère suggested_hooks de VideoInsights
       - Adapte au style détecté (ajoute emojis, caps, catchphrases)
       - Si hook_type = emoji_start → place emoji au début
    
    2. BODY
       - Génère teaser basé sur energy level
       - High energy: "J'ai passé des heures...", "Ça va te choquer"
       - Medium: "Check ce que j'ai fait", "Nouvelle vidéo"
    
    3. CTA
       - Si structure inclut CTA:
         - Twitter: "🔗 Vidéo complète ci-dessous"
         - Instagram: "🔗 Lien dans bio"
    
    4. EMOJIS
       - Selon frequency et placement
       - Utilise favorite_emojis
    
    5. HASHTAGS
       - Si uses_hashtags = true
       - Génère hashtag_count_avg hashtags
       - Basé sur content_type + popular tags
    
    6. AJUSTE LONGUEUR
       - Twitter: max 280 chars
       - Instagram: max 2200 chars
    
    7. VALIDE STYLE MATCH
       - Score 0-1
    """
```

---

## 📈 Confidence Score

Score 0-1 basé sur nombre de training posts:

- **50+ posts**: 1.0 confidence (excellent)
- **20-49 posts**: 0.9 confidence (très bon)
- **10-19 posts**: 0.75 confidence (bon)
- **5-9 posts**: 0.6 confidence (acceptable)
- **<5 posts**: 0.4 confidence (insuffisant - besoin de plus de training)

---

## 🚀 Workflow Recommandé

### Phase 1: Training Initial

```bash
# 1. Collecte tes meilleurs posts (20-50 minimum)
# 2. Entraîne le modèle
curl -X POST /style/train -d '{"posts": [...]}'

# 3. Analyse le style
curl -X POST /style/analyze

# 4. Vérifie le profile
curl -X GET /style/profile
```

### Phase 2: Génération

```bash
# Pour chaque nouvelle vidéo:
curl -X POST /style/generate \
  -d '{"video_id": "123", "platform": "twitter"}'

# Si style_match_score < 0.7:
#   - Affine les training posts
#   - Re-run /style/analyze
```

### Phase 3: Validation Continue

```bash
# Avant de publier:
curl -X POST /style/validate \
  -d '{"post_text": "ton post généré"}'

# Si score < 0.8:
#   - Ajuste manuellement
#   - Ou ajoute ce post au training pour améliorer
```

---

## 🔄 Intégration avec Content Scheduler

Le Style Learner sera utilisé par le **Content Scheduler** pour:

1. **Auto-génération posts programmés**
   - Scheduler récupère VideoInsights
   - Appelle `/style/generate` pour chaque platform
   - Valide avec `/style/validate`
   - Programme publication

2. **Adaptation multi-platform**
   - Twitter: 280 chars, hooks accrocheurs, 2-3 hashtags
   - Instagram: 2200 chars, plus long body, CTA "lien dans bio"
   - Facebook: Style plus conversationnel
   - LinkedIn: Tone plus professionnel (formality +2)
   - Bluesky: Authentique, casual

3. **A/B Testing**
   - Génère 3-5 variations
   - Valide chaque variation
   - Garde les 2 meilleures (score >0.8)
   - Track performance réelle

---

## 🐛 Debugging

### Si confidence < 0.6:
- Ajoute plus de training posts (target 20+)
- Assure-toi que les posts sont représentatifs de TON style
- Vérifie diversité: différents hooks, structures, platforms

### Si style_match_score toujours bas (<0.6):
```python
# Check le profile détaillé:
profile = analyzer.style_profile

# Analyse manuelle:
print(f"Energy: {profile.energy}")        # Trop bas/haut?
print(f"Emojis: {profile.emoji_frequency}")  # Match pas?
print(f"Catchphrases: {profile.catchphrases}")  # Utilisées?
```

### Si génération semble off:
- Vérifie que VideoInsights sont corrects (engagement, content_type)
- Teste avec différentes vidéos (tutorial vs vlog vs teaser)
- Ajuste manuellement et ajoute au training

---

## 📝 Exemple Complet

```python
# Training
analyzer = StyleAnalyzerAI()

posts = [
    "🔥 OK LES GARS - J'ai découvert un truc INSANE...",
    "💡 Cette technique va te choquer - GAME CHANGER...",
    "YO! 👀 J'ai passé 5h sur ce projet... FOU 🔥"
]

for post in posts:
    analyzer.add_training_post(post, platform="twitter")

# Analyze
profile = analyzer.analyze_style()
print(f"Confidence: {profile.confidence_score:.0%}")
print(f"Energy: {profile.energy}/10")
print(f"Favorite emojis: {profile.favorite_emojis[:5]}")

# Generate
video_insights = {
    "title": "Edit like a PRO",
    "content_type": "tutorial",
    "engagement_score": 8.5,
    "suggested_hooks": ["🎬 Master video editing in 10 minutes"]
}

post = analyzer.generate_post(video_insights, platform="twitter")
print(f"\nGenerated:\n{post}")

# Validate
score = analyzer.validate_style_match(post)
print(f"\nStyle Match: {score:.0%}")
```

**Output:**
```
Confidence: 60%
Energy: 8/10
Favorite emojis: ['🔥', '👇', '💡', '👀', '😱']

Generated:
🔥 OK LES GARS

J'ai passé des heures sur Edit like a PRO

Tu vas kiffer 💯

🔗 Vidéo complète ci-dessous

#tutorial #insane

Style Match: 85%
```

---

## 🎯 Next Steps

1. **Collecte tes posts réels** - Export Twitter/IG via API ou manual
2. **Train le modèle** - Minimum 10 posts, target 20+
3. **Test génération** - Sur 3-5 vidéos différentes
4. **Affine** - Ajuste training set si style_match < 0.8
5. **Intègre au Scheduler** - Auto-génération posts programmés

---

## 🔗 Liens

- **Video Analyzer**: `video_analyzer.py` - Analyse vidéos, génère hooks
- **Content Brain API**: `content_brain.py` - 11 endpoints (6 video + 5 style)
- **Next**: Content Scheduler - Automatise posting avec style personnalisé
