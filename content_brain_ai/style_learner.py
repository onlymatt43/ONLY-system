"""
Style Learner AI - Analyse et réplique ton style d'écriture unique
Capture tone, vocabulary, expressions, emojis, structure de posts
"""

import re
import json
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict


# ==================== DATA MODELS ====================

@dataclass
class StyleProfile:
    """Profil de style d'écriture unique"""
    
    # Patterns linguistiques
    vocabulary_level: str  # casual, professional, expert
    sentence_length: str  # short, medium, long
    punctuation_style: str  # minimal, standard, expressive
    
    # Ton & voix
    tone: List[str]  # [friendly, direct, humorous, energetic]
    formality: int  # 0-10 (0=très casual, 10=très formel)
    energy: int  # 0-10 (0=calme, 10=hyper énergique)
    
    # Expressions signature
    catchphrases: List[str]  # Expressions récurrentes
    common_words: List[str]  # Mots fréquents
    
    # Emojis
    emoji_frequency: str  # none, low, medium, high
    favorite_emojis: List[str]  # Top emojis utilisés
    emoji_placement: str  # start, end, inline, mixed
    
    # Structure posts
    typical_structure: List[str]  # [hook, body, cta, link]
    avg_post_length: int  # caractères
    uses_hashtags: bool
    hashtag_count_avg: int
    
    # Hooks préférés
    hook_types: List[str]  # Types de hooks utilisés
    hook_examples: List[str]  # Exemples concrets
    
    # Métadonnées
    analyzed_posts_count: int
    confidence_score: float  # 0-1


# ==================== STYLE ANALYZER ====================

class StyleAnalyzerAI:
    """Analyse et apprend ton style d'écriture"""
    
    def __init__(self):
        self.training_posts = []
        self.style_profile = None
        
        # Hook patterns communs
        self.hook_patterns = {
            "question": r"^\?|^Comment |^Pourquoi |^Quand |^Qui |^Quoi ",
            "emoji_start": r"^[😀-🙏💀-🙏🚀-🛸🔥⚡💎💯✨👀🎯]",
            "caps_statement": r"^[A-Z\s]{10,}",
            "exclamation": r"^[^\n]+!",
            "number": r"^\d+",
            "direct_address": r"^(OK|YO|HEY|LES GARS|REGARDE|CHECK)"
        }
    
    def add_training_post(self, post_text: str, platform: str = "twitter"):
        """Ajoute un post à l'entraînement"""
        self.training_posts.append({
            "text": post_text,
            "platform": platform,
            "length": len(post_text)
        })
    
    def add_training_posts_batch(self, posts: List[Dict[str, str]]):
        """Ajoute plusieurs posts d'un coup"""
        for post in posts:
            self.add_training_post(post.get("text", ""), post.get("platform", "twitter"))
    
    def analyze_style(self) -> StyleProfile:
        """
        Analyse tous les posts et génère StyleProfile
        
        Returns:
            StyleProfile avec patterns détectés
        """
        
        if not self.training_posts:
            raise ValueError("No training posts added. Use add_training_post() first.")
        
        posts_text = [p["text"] for p in self.training_posts]
        
        # 1. Analyse vocabulaire et phrases
        vocab_analysis = self._analyze_vocabulary(posts_text)
        
        # 2. Analyse ton et énergie
        tone_analysis = self._analyze_tone(posts_text)
        
        # 3. Analyse emojis
        emoji_analysis = self._analyze_emojis(posts_text)
        
        # 4. Analyse structure
        structure_analysis = self._analyze_structure(posts_text)
        
        # 5. Analyse hooks
        hook_analysis = self._analyze_hooks(posts_text)
        
        # 6. Calcule confidence
        confidence = self._calculate_confidence()
        
        # Compile StyleProfile
        self.style_profile = StyleProfile(
            vocabulary_level=vocab_analysis["level"],
            sentence_length=vocab_analysis["sentence_length"],
            punctuation_style=vocab_analysis["punctuation"],
            tone=tone_analysis["tones"],
            formality=tone_analysis["formality"],
            energy=tone_analysis["energy"],
            catchphrases=vocab_analysis["catchphrases"],
            common_words=vocab_analysis["common_words"],
            emoji_frequency=emoji_analysis["frequency"],
            favorite_emojis=emoji_analysis["favorites"],
            emoji_placement=emoji_analysis["placement"],
            typical_structure=structure_analysis["structure"],
            avg_post_length=structure_analysis["avg_length"],
            uses_hashtags=structure_analysis["uses_hashtags"],
            hashtag_count_avg=structure_analysis["hashtag_avg"],
            hook_types=hook_analysis["types"],
            hook_examples=hook_analysis["examples"],
            analyzed_posts_count=len(self.training_posts),
            confidence_score=confidence
        )
        
        return self.style_profile
    
    def _analyze_vocabulary(self, posts: List[str]) -> Dict:
        """Analyse vocabulaire et patterns linguistiques"""
        
        all_text = " ".join(posts).lower()
        words = re.findall(r'\b\w+\b', all_text)
        
        # Mots communs (exclude stop words basiques)
        stop_words = {"le", "la", "les", "un", "une", "des", "et", "ou", "mais", 
                     "de", "du", "à", "au", "pour", "sur", "dans", "avec"}
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        word_counts = Counter(meaningful_words)
        common_words = [w for w, c in word_counts.most_common(15)]
        
        # Catchphrases (2-3 word phrases récurrentes)
        catchphrases = []
        for post in posts:
            # Patterns de 2-4 mots en caps ou avec emojis
            patterns = re.findall(r'(?:[A-Z\s]{5,20}|[\w\s]{3,15}[!]{2,})', post)
            catchphrases.extend([p.strip() for p in patterns if len(p.strip()) > 4])
        
        catchphrase_counts = Counter(catchphrases)
        top_catchphrases = [c for c, count in catchphrase_counts.most_common(10) if count >= 2]
        
        # Vocabulary level (basé sur mots complexes)
        complex_words = [w for w in words if len(w) > 8]
        complexity_ratio = len(complex_words) / max(len(words), 1)
        
        if complexity_ratio > 0.15:
            vocab_level = "expert"
        elif complexity_ratio > 0.08:
            vocab_level = "professional"
        else:
            vocab_level = "casual"
        
        # Sentence length
        sentences = []
        for post in posts:
            sents = re.split(r'[.!?]+', post)
            sentences.extend([s.strip() for s in sents if s.strip()])
        
        if sentences:
            avg_sent_length = statistics.mean([len(s.split()) for s in sentences])
            if avg_sent_length < 8:
                sent_length = "short"
            elif avg_sent_length < 15:
                sent_length = "medium"
            else:
                sent_length = "long"
        else:
            sent_length = "short"
        
        # Punctuation style
        exclamation_count = all_text.count('!')
        question_count = all_text.count('?')
        total_chars = len(all_text)
        
        punctuation_ratio = (exclamation_count + question_count) / max(total_chars, 1) * 1000
        
        if punctuation_ratio > 15:
            punctuation = "expressive"
        elif punctuation_ratio > 5:
            punctuation = "standard"
        else:
            punctuation = "minimal"
        
        return {
            "level": vocab_level,
            "sentence_length": sent_length,
            "punctuation": punctuation,
            "common_words": common_words[:10],
            "catchphrases": top_catchphrases[:5]
        }
    
    def _analyze_tone(self, posts: List[str]) -> Dict:
        """Analyse ton et énergie"""
        
        all_text = " ".join(posts).lower()
        
        # Détecte tones via mots-clés
        tones = []
        
        # Friendly
        friendly_words = ["merci", "cool", "super", "génial", "love", "kiff"]
        if any(w in all_text for w in friendly_words):
            tones.append("friendly")
        
        # Direct
        direct_patterns = ["regarde", "check", "écoute", "fais", "va", "prend"]
        if any(w in all_text for w in direct_patterns):
            tones.append("direct")
        
        # Humorous
        humor_indicators = ["😂", "lol", "mdr", "haha", "🤣"]
        if any(i in all_text for i in humor_indicators):
            tones.append("humorous")
        
        # Energetic
        energy_words = ["insane", "fou", "incroyable", "choquant", "🔥", "⚡"]
        if any(w in all_text for w in energy_words):
            tones.append("energetic")
        
        if not tones:
            tones = ["neutral"]
        
        # Formality (0-10)
        formal_indicators = ["veuillez", "cordialement", "monsieur", "madame"]
        casual_indicators = ["yo", "mec", "gars", "bro", "kiff"]
        
        formality_score = 5  # baseline
        if any(w in all_text for w in formal_indicators):
            formality_score += 3
        if any(w in all_text for w in casual_indicators):
            formality_score -= 3
        
        formality_score = max(0, min(10, formality_score))
        
        # Energy level (0-10)
        energy_score = 5  # baseline
        
        # Caps usage
        caps_ratio = sum(1 for c in all_text if c.isupper()) / max(len(all_text), 1)
        if caps_ratio > 0.1:
            energy_score += 2
        
        # Exclamation marks
        exclamation_ratio = all_text.count('!') / max(len(all_text), 1) * 100
        if exclamation_ratio > 1.5:
            energy_score += 2
        
        # Energy emojis
        energy_emojis = ["🔥", "⚡", "💥", "🚀", "💯"]
        if any(e in all_text for e in energy_emojis):
            energy_score += 1
        
        energy_score = max(0, min(10, energy_score))
        
        return {
            "tones": tones,
            "formality": formality_score,
            "energy": energy_score
        }
    
    def _analyze_emojis(self, posts: List[str]) -> Dict:
        """Analyse usage emojis"""
        
        all_text = " ".join(posts)
        
        # Extraire tous les emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        emojis = emoji_pattern.findall(all_text)
        
        if not emojis:
            return {
                "frequency": "none",
                "favorites": [],
                "placement": "none"
            }
        
        # Frequency
        emoji_count = len(emojis)
        post_count = len(posts)
        emojis_per_post = emoji_count / post_count
        
        if emojis_per_post >= 3:
            frequency = "high"
        elif emojis_per_post >= 1:
            frequency = "medium"
        else:
            frequency = "low"
        
        # Favorites
        emoji_counts = Counter(emojis)
        favorites = [e for e, c in emoji_counts.most_common(10)]
        
        # Placement
        start_count = 0
        end_count = 0
        inline_count = 0
        
        for post in posts:
            post_emojis = emoji_pattern.findall(post)
            if not post_emojis:
                continue
            
            # Check first 20 chars
            if emoji_pattern.search(post[:20]):
                start_count += 1
            # Check last 20 chars
            if emoji_pattern.search(post[-20:]):
                end_count += 1
            # Check middle
            if len(post) > 40 and emoji_pattern.search(post[20:-20]):
                inline_count += 1
        
        if start_count > end_count and start_count > inline_count:
            placement = "start"
        elif end_count > start_count and end_count > inline_count:
            placement = "end"
        elif inline_count > 0:
            placement = "inline"
        else:
            placement = "mixed"
        
        return {
            "frequency": frequency,
            "favorites": favorites,
            "placement": placement
        }
    
    def _analyze_structure(self, posts: List[str]) -> Dict:
        """Analyse structure des posts"""
        
        # Average length
        avg_length = statistics.mean([len(p) for p in posts])
        
        # Hashtags
        all_hashtags = []
        posts_with_hashtags = 0
        
        for post in posts:
            hashtags = re.findall(r'#\w+', post)
            if hashtags:
                posts_with_hashtags += 1
                all_hashtags.extend(hashtags)
        
        uses_hashtags = posts_with_hashtags > len(posts) * 0.3
        hashtag_avg = len(all_hashtags) / len(posts) if posts else 0
        
        # Structure patterns
        structure_elements = []
        
        # Détecte si posts ont généralement un hook
        hooks_count = sum(1 for p in posts if self._has_hook(p))
        if hooks_count > len(posts) * 0.5:
            structure_elements.append("hook")
        
        # Détecte body
        structure_elements.append("body")
        
        # Détecte CTA
        cta_patterns = ["regarde", "check", "clique", "voir", "achète", "obtiens"]
        cta_count = sum(1 for p in posts if any(c in p.lower() for c in cta_patterns))
        if cta_count > len(posts) * 0.3:
            structure_elements.append("cta")
        
        # Détecte links
        link_count = sum(1 for p in posts if "http" in p or ".com" in p)
        if link_count > len(posts) * 0.3:
            structure_elements.append("link")
        
        return {
            "structure": structure_elements,
            "avg_length": int(avg_length),
            "uses_hashtags": uses_hashtags,
            "hashtag_avg": round(hashtag_avg, 1)
        }
    
    def _analyze_hooks(self, posts: List[str]) -> Dict:
        """Analyse types de hooks utilisés"""
        
        hook_types_detected = []
        hook_examples = []
        
        for post in posts:
            # Prend première ligne comme hook
            first_line = post.split('\n')[0] if '\n' in post else post[:100]
            
            # Détecte type de hook
            for hook_type, pattern in self.hook_patterns.items():
                if re.search(pattern, first_line, re.IGNORECASE):
                    hook_types_detected.append(hook_type)
                    if len(hook_examples) < 5:
                        hook_examples.append(first_line[:80])
                    break
        
        # Count types
        hook_type_counts = Counter(hook_types_detected)
        top_hook_types = [t for t, c in hook_type_counts.most_common(5)]
        
        return {
            "types": top_hook_types if top_hook_types else ["statement"],
            "examples": hook_examples[:5]
        }
    
    def _has_hook(self, post: str) -> bool:
        """Vérifie si post commence par un hook"""
        first_line = post.split('\n')[0] if '\n' in post else post[:100]
        
        for pattern in self.hook_patterns.values():
            if re.search(pattern, first_line, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_confidence(self) -> float:
        """Calcule score de confiance (0-1)"""
        
        post_count = len(self.training_posts)
        
        # Plus de posts = plus de confiance
        if post_count >= 50:
            confidence = 1.0
        elif post_count >= 20:
            confidence = 0.9
        elif post_count >= 10:
            confidence = 0.75
        elif post_count >= 5:
            confidence = 0.6
        else:
            confidence = 0.4
        
        return confidence
    
    def generate_post(
        self,
        video_insights: Dict,
        platform: str = "twitter",
        style_override: Optional[Dict] = None
    ) -> str:
        """
        Génère post dans TON style basé sur VideoInsights
        
        Args:
            video_insights: Dict de VideoInsights (engagement, hooks, etc.)
            platform: Platform cible
            style_override: Override certains éléments de style
            
        Returns:
            Post généré dans ton style
        """
        
        if not self.style_profile:
            raise ValueError("Style not analyzed yet. Call analyze_style() first.")
        
        profile = self.style_profile
        
        # Récupère hooks suggérés de video_insights
        suggested_hooks = video_insights.get("suggested_hooks", [])
        video_title = video_insights.get("title", "cette vidéo")
        
        # 1. Génère hook dans ton style
        if profile.hook_types:
            hook_type = profile.hook_types[0]
        else:
            hook_type = "emoji_start"
        
        if suggested_hooks:
            # Adapte hook suggéré à ton style
            base_hook = suggested_hooks[0]
            hook = self._adapt_hook_to_style(base_hook, profile)
        else:
            # Génère hook from scratch
            hook = self._generate_hook_from_style(video_title, profile)
        
        # 2. Génère body
        body_parts = []
        
        # Ajoute teasing/context
        if profile.energy >= 7:
            teasers = [
                f"J'ai passé des heures sur {video_title}...",
                f"Tu vas pas croire ce que j'ai découvert",
                f"Ça va te choquer"
            ]
        else:
            teasers = [
                f"Check ce que j'ai fait avec {video_title}",
                f"Nouvelle vidéo sur {video_title}",
                f"Tu devrais voir ça"
            ]
        
        body_parts.append(teasers[0])
        
        # 3. Génère CTA
        if "cta" in profile.typical_structure:
            if platform == "twitter":
                cta = "🔗 Vidéo complète ci-dessous"
            elif platform == "instagram":
                cta = "🔗 Lien dans bio"
            else:
                cta = "Regarde maintenant 👇"
        else:
            cta = ""
        
        # 4. Assemble post
        post_parts = [hook]
        
        if body_parts:
            post_parts.append("\n\n" + "\n".join(body_parts))
        
        if cta:
            post_parts.append("\n\n" + cta)
        
        # 5. Ajoute emojis selon style
        if profile.emoji_frequency in ["medium", "high"]:
            post_parts = self._add_emojis_to_post(post_parts, profile)
        
        # 6. Ajoute hashtags si utilisés
        if profile.uses_hashtags and platform in ["twitter", "instagram"]:
            hashtags = self._generate_hashtags(video_insights, profile)
            if hashtags:
                post_parts.append("\n\n" + " ".join(hashtags))
        
        final_post = "".join(post_parts)
        
        # 7. Ajuste longueur selon plateforme
        if platform == "twitter" and len(final_post) > 280:
            final_post = final_post[:277] + "..."
        
        return final_post
    
    def _adapt_hook_to_style(self, hook: str, profile: StyleProfile) -> str:
        """Adapte hook suggéré à ton style"""
        
        # Ajoute emojis si ton style les utilise au début
        if profile.emoji_placement in ["start", "mixed"] and profile.favorite_emojis:
            if not any(e in hook for e in profile.favorite_emojis[:5]):
                hook = f"{profile.favorite_emojis[0]} {hook}"
        
        # Ajuste energy
        if profile.energy >= 8:
            # Ajoute caps ou exclamations
            if "!" not in hook:
                hook = hook.rstrip(".?") + "!"
        
        # Ajoute catchphrase si possible
        if profile.catchphrases and len(hook) < 100:
            hook = f"{profile.catchphrases[0].upper()} - {hook}"
        
        return hook
    
    def _generate_hook_from_style(self, topic: str, profile: StyleProfile) -> str:
        """Génère hook from scratch dans ton style"""
        
        hooks = []
        
        # High energy hooks
        if profile.energy >= 7:
            if profile.favorite_emojis:
                emoji = profile.favorite_emojis[0]
                hooks.append(f"{emoji} OK LES GARS")
                hooks.append(f"{emoji} TU DOIS VOIR ÇA")
                hooks.append(f"{emoji} C'EST INSANE")
        
        # Medium energy hooks
        else:
            hooks.append(f"Check {topic}")
            hooks.append(f"Nouvelle vidéo : {topic}")
        
        return hooks[0] if hooks else f"🔥 {topic}"
    
    def _add_emojis_to_post(self, parts: List[str], profile: StyleProfile) -> List[str]:
        """Ajoute emojis selon style"""
        
        if not profile.favorite_emojis:
            return parts
        
        # Ajoute quelques emojis dans le body
        emojis_to_add = profile.favorite_emojis[:3]
        
        # Simple: ajoute emojis inline
        for i, part in enumerate(parts):
            if i > 0 and len(part) > 30:  # Pas le hook
                # Ajoute emoji aléatoirement
                if "résultat" in part.lower() or "découvert" in part.lower():
                    parts[i] = part.replace("résultat", f"{emojis_to_add[0]} résultat")
        
        return parts
    
    def _generate_hashtags(self, video_insights: Dict, profile: StyleProfile) -> List[str]:
        """Génère hashtags pertinents"""
        
        hashtags = []
        
        # Basé sur content type
        content_type = video_insights.get("content_type", "")
        if content_type:
            hashtags.append(f"#{content_type}")
        
        # Generic popular tags
        popular = ["#viral", "#insane", "#tutorial", "#fyp"]
        hashtags.extend(popular[:2])
        
        # Limite au avg du profile
        max_tags = int(profile.hashtag_count_avg) + 1
        
        return hashtags[:max_tags]
    
    def validate_style_match(self, generated_post: str) -> float:
        """
        Valide si post généré match ton style
        
        Args:
            generated_post: Post à valider
            
        Returns:
            Score 0-1 (0=pas ton style, 1=parfait match)
        """
        
        if not self.style_profile:
            return 0.5
        
        profile = self.style_profile
        score = 0.5  # baseline
        checks = 0
        
        # Check 1: Emoji usage
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            "]+", flags=re.UNICODE)
        
        emojis_in_post = emoji_pattern.findall(generated_post)
        
        if profile.emoji_frequency == "high" and len(emojis_in_post) >= 2:
            score += 0.1
        elif profile.emoji_frequency == "medium" and 0 < len(emojis_in_post) < 3:
            score += 0.1
        elif profile.emoji_frequency in ["none", "low"] and len(emojis_in_post) == 0:
            score += 0.1
        checks += 1
        
        # Check 2: Length
        post_length = len(generated_post)
        length_diff = abs(post_length - profile.avg_post_length)
        
        if length_diff < profile.avg_post_length * 0.3:
            score += 0.15
        checks += 1
        
        # Check 3: Energy (caps & exclamation)
        caps_ratio = sum(1 for c in generated_post if c.isupper()) / max(len(generated_post), 1)
        exclamation_count = generated_post.count('!')
        
        if profile.energy >= 7:
            if caps_ratio > 0.05 or exclamation_count >= 1:
                score += 0.1
        else:
            if caps_ratio < 0.1 and exclamation_count <= 2:
                score += 0.1
        checks += 1
        
        # Check 4: Common words usage
        post_lower = generated_post.lower()
        common_words_found = sum(1 for w in profile.common_words if w in post_lower)
        
        if common_words_found >= 2:
            score += 0.1
        checks += 1
        
        # Check 5: Catchphrases
        catchphrases_found = sum(1 for c in profile.catchphrases if c.lower() in post_lower)
        if catchphrases_found >= 1:
            score += 0.15
        checks += 1
        
        return min(1.0, score)


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """Test du Style Learner"""
    
    print("✍️ Style Learner AI - Test")
    print("=" * 50)
    
    # Exemple: posts d'entraînement
    example_posts = [
        "🔥 OK LES GARS\n\nJ'ai découvert un truc INSANE pour éditer 10x plus vite\n\nRegarde ça 👇\n\n#tutorial #editing",
        "💡 Cette technique va te choquer\n\nPersonne n'en parle mais c'est GAME CHANGER\n\nVideo complète: only.com/123",
        "YO! 👀\n\nJ'ai passé 5h sur ce projet...\n\nLe résultat? FOU 🔥\n\nCheck la vidéo #insane",
        "😱 TU DOIS VOIR ÇA\n\nLa méthode que tous les pros utilisent\n\nTu vas kiffer 💯",
        "🎯 Comment j'ai fait ça en 10 minutes?\n\nLaisse-moi te montrer\n\nC'est plus simple que tu penses 💎"
    ]
    
    # Initialize
    analyzer = StyleAnalyzerAI()
    
    # Add training posts
    for post in example_posts:
        analyzer.add_training_post(post, platform="twitter")
    
    print(f"\n📚 {len(example_posts)} posts ajoutés pour training")
    
    # Analyze style
    print("\n🔍 Analyse du style...")
    profile = analyzer.analyze_style()
    
    print(f"\n✅ Style Profile généré!")
    print(f"\n📊 Résumé:")
    print(f"  Vocabulary: {profile.vocabulary_level}")
    print(f"  Sentence length: {profile.sentence_length}")
    print(f"  Tone: {', '.join(profile.tone)}")
    print(f"  Formality: {profile.formality}/10")
    print(f"  Energy: {profile.energy}/10")
    print(f"  Emoji frequency: {profile.emoji_frequency}")
    print(f"  Favorite emojis: {' '.join(profile.favorite_emojis[:5])}")
    print(f"  Catchphrases: {profile.catchphrases}")
    print(f"  Hook types: {profile.hook_types}")
    print(f"  Confidence: {profile.confidence_score:.0%}")
    
    # Generate post
    print("\n\n🎨 Génération post dans TON style...")
    
    fake_video_insights = {
        "title": "Edit like a PRO",
        "content_type": "tutorial",
        "engagement_score": 8.5,
        "suggested_hooks": ["🎬 Master video editing in 10 minutes"]
    }
    
    generated_post = analyzer.generate_post(fake_video_insights, platform="twitter")
    
    print(f"\n📝 Post généré:")
    print("=" * 50)
    print(generated_post)
    print("=" * 50)
    
    # Validate
    match_score = analyzer.validate_style_match(generated_post)
    print(f"\n✅ Style Match Score: {match_score:.0%}")
    
    if match_score >= 0.8:
        print("💯 Excellent match - sonne exactement comme toi!")
    elif match_score >= 0.6:
        print("👍 Bon match - quelques ajustements mineurs")
    else:
        print("⚠️ Besoin de plus de training posts")
