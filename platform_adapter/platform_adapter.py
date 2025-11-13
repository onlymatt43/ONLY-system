"""
Platform Adapter - Optimise contenu pour chaque plateforme
Twitter, Instagram, Facebook, LinkedIn, Bluesky - specs spécifiques
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


# ==================== ENUMS ====================

class Platform(str, Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    BLUESKY = "bluesky"


class AspectRatio(str, Enum):
    VERTICAL = "9:16"      # Stories, Reels, TikTok
    SQUARE = "1:1"         # Feed posts
    HORIZONTAL = "16:9"    # YouTube, Facebook
    PORTRAIT = "4:5"       # IG portrait feed


# ==================== PLATFORM SPECS ====================

@dataclass
class PlatformSpec:
    """Spécifications techniques d'une plateforme"""
    
    platform: str
    
    # Text limits
    max_text_length: int
    optimal_text_length: int
    
    # Video specs
    max_video_duration: int  # seconds
    optimal_video_duration: int
    preferred_aspect_ratios: List[str]
    
    # Content features
    supports_hashtags: bool
    max_hashtags: int
    supports_links: bool
    link_placement: str  # "inline", "bio", "caption_end"
    
    # Style guidelines
    tone: str  # "casual", "professional", "authentic"
    emoji_usage: str  # "high", "medium", "low"
    caption_style: str  # "short_punchy", "storytelling", "informative"
    
    # Best practices
    optimal_posting_hours: List[int]
    call_to_action_style: str


# Platform specifications database
PLATFORM_SPECS = {
    Platform.TWITTER: PlatformSpec(
        platform="twitter",
        max_text_length=280,
        optimal_text_length=200,
        max_video_duration=140,
        optimal_video_duration=30,
        preferred_aspect_ratios=[AspectRatio.VERTICAL, AspectRatio.SQUARE],
        supports_hashtags=True,
        max_hashtags=3,
        supports_links=True,
        link_placement="inline",
        tone="casual",
        emoji_usage="high",
        caption_style="short_punchy",
        optimal_posting_hours=[9, 12, 15, 18, 21],
        call_to_action_style="direct"
    ),
    
    Platform.INSTAGRAM: PlatformSpec(
        platform="instagram",
        max_text_length=2200,
        optimal_text_length=150,
        max_video_duration=90,
        optimal_video_duration=60,
        preferred_aspect_ratios=[AspectRatio.VERTICAL, AspectRatio.PORTRAIT],
        supports_hashtags=True,
        max_hashtags=10,
        supports_links=False,
        link_placement="bio",
        tone="casual",
        emoji_usage="high",
        caption_style="storytelling",
        optimal_posting_hours=[11, 13, 19, 21],
        call_to_action_style="soft"
    ),
    
    Platform.FACEBOOK: PlatformSpec(
        platform="facebook",
        max_text_length=63206,
        optimal_text_length=250,
        max_video_duration=240,
        optimal_video_duration=90,
        preferred_aspect_ratios=[AspectRatio.HORIZONTAL, AspectRatio.SQUARE],
        supports_hashtags=True,
        max_hashtags=5,
        supports_links=True,
        link_placement="inline",
        tone="casual",
        emoji_usage="medium",
        caption_style="storytelling",
        optimal_posting_hours=[9, 13, 15, 18],
        call_to_action_style="conversational"
    ),
    
    Platform.LINKEDIN: PlatformSpec(
        platform="linkedin",
        max_text_length=3000,
        optimal_text_length=200,
        max_video_duration=600,
        optimal_video_duration=45,
        preferred_aspect_ratios=[AspectRatio.HORIZONTAL, AspectRatio.SQUARE],
        supports_hashtags=True,
        max_hashtags=5,
        supports_links=True,
        link_placement="inline",
        tone="professional",
        emoji_usage="low",
        caption_style="informative",
        optimal_posting_hours=[8, 12, 17],
        call_to_action_style="professional"
    ),
    
    Platform.BLUESKY: PlatformSpec(
        platform="bluesky",
        max_text_length=300,
        optimal_text_length=250,
        max_video_duration=60,
        optimal_video_duration=45,
        preferred_aspect_ratios=[AspectRatio.VERTICAL, AspectRatio.SQUARE],
        supports_hashtags=True,
        max_hashtags=4,
        supports_links=True,
        link_placement="inline",
        tone="authentic",
        emoji_usage="medium",
        caption_style="short_punchy",
        optimal_posting_hours=[10, 14, 20],
        call_to_action_style="authentic"
    )
}


# ==================== DATA MODELS ====================

@dataclass
class AdaptedContent:
    """Contenu adapté pour une plateforme"""
    
    platform: str
    
    # Text content
    caption: str
    caption_length: int
    
    # Hashtags
    hashtags: List[str]
    hashtag_count: int
    
    # Video specs
    video_duration: int
    aspect_ratio: str
    needs_captions: bool
    
    # Links
    link: Optional[str]
    link_placement: str
    
    # Metadata
    estimated_engagement: float  # 0-10
    optimization_score: float  # 0-1 (compliance with platform specs)
    
    # Recommendations
    recommendations: List[str]


@dataclass
class VideoSegment:
    """Segment vidéo optimisé pour platform"""
    
    start_time: int
    end_time: int
    duration: int
    aspect_ratio: str
    needs_captions: bool
    recommended_text_overlay: Optional[str]


# ==================== PLATFORM ADAPTER ====================

class PlatformAdapter:
    """Adapte contenu pour optimisation platform-specific"""
    
    def __init__(self):
        self.specs = PLATFORM_SPECS
        
        # CTA templates par platform
        self.cta_templates = {
            Platform.TWITTER: [
                "👇 Thread complet",
                "🔗 Regarde maintenant",
                "💬 RT si tu kiffes"
            ],
            Platform.INSTAGRAM: [
                "🔗 Lien dans bio",
                "👆 Swipe up",
                "💬 Partage en story si tu aimes"
            ],
            Platform.FACEBOOK: [
                "👉 Clique pour voir la suite",
                "💬 Partage avec tes amis",
                "🔔 Active les notifications"
            ],
            Platform.LINKEDIN: [
                "🔗 En savoir plus",
                "💬 Qu'en pensez-vous?",
                "📊 Partagez votre expérience"
            ],
            Platform.BLUESKY: [
                "👇 Plus d'infos",
                "💬 Dis-moi ce que tu en penses",
                "🔄 Repost si pertinent"
            ]
        }
    
    def adapt_content(
        self,
        base_content: str,
        platform: Platform,
        video_duration: Optional[int] = None,
        style_profile: Optional[Dict] = None,
        link: Optional[str] = None
    ) -> AdaptedContent:
        """
        Adapte contenu pour plateforme spécifique
        
        Args:
            base_content: Contenu original (généré par Style Learner)
            platform: Platform cible
            video_duration: Durée vidéo (seconds)
            style_profile: StyleProfile du user
            link: Lien à inclure
            
        Returns:
            AdaptedContent optimisé
        """
        
        spec = self.specs[platform]
        
        # 1. Adapte caption
        caption = self._adapt_caption(
            base_content, spec, style_profile
        )
        
        # 2. Extrait/génère hashtags
        hashtags = self._extract_hashtags(caption)
        if len(hashtags) > spec.max_hashtags:
            hashtags = hashtags[:spec.max_hashtags]
        
        # Remove hashtags from caption si trop
        if len(hashtags) > spec.max_hashtags:
            for tag in hashtags[spec.max_hashtags:]:
                caption = caption.replace(tag, "").strip()
        
        # 3. Ajoute CTA approprié
        caption = self._add_cta(caption, platform, spec)
        
        # 4. Handle link placement
        link_placement = spec.link_placement
        if link and spec.supports_links:
            if link_placement == "inline":
                # Ajoute link à la fin si pas déjà présent
                if link not in caption:
                    caption = f"{caption}\n\n🔗 {link}"
            elif link_placement == "caption_end":
                caption = f"{caption}\n\n{link}"
            # "bio" = pas dans caption
        
        # 5. Ajuste longueur caption
        if len(caption) > spec.max_text_length:
            caption = self._truncate_caption(caption, spec.max_text_length)
        
        # 6. Recommande aspect ratio & duration
        aspect_ratio = spec.preferred_aspect_ratios[0]
        recommended_duration = spec.optimal_video_duration
        
        if video_duration:
            recommended_duration = min(video_duration, spec.optimal_video_duration)
        
        # 7. Needs captions? (Facebook toujours, LinkedIn souvent)
        needs_captions = platform in [Platform.FACEBOOK, Platform.LINKEDIN]
        
        # 8. Calculate scores
        optimization_score = self._calculate_optimization_score(
            caption, hashtags, spec, video_duration
        )
        
        estimated_engagement = self._estimate_engagement(
            platform, optimization_score, len(hashtags)
        )
        
        # 9. Generate recommendations
        recommendations = self._generate_recommendations(
            caption, hashtags, spec, video_duration, optimization_score
        )
        
        return AdaptedContent(
            platform=platform.value,
            caption=caption,
            caption_length=len(caption),
            hashtags=hashtags,
            hashtag_count=len(hashtags),
            video_duration=recommended_duration,
            aspect_ratio=aspect_ratio,
            needs_captions=needs_captions,
            link=link if spec.supports_links else None,
            link_placement=link_placement,
            estimated_engagement=estimated_engagement,
            optimization_score=optimization_score,
            recommendations=recommendations
        )
    
    def _adapt_caption(
        self,
        content: str,
        spec: PlatformSpec,
        style_profile: Optional[Dict]
    ) -> str:
        """Adapte caption selon platform specs"""
        
        caption = content
        
        # Ajuste tone selon platform
        if spec.tone == "professional":
            # LinkedIn - plus formel
            caption = self._make_professional(caption)
        
        elif spec.tone == "authentic":
            # Bluesky - authentique, pas trop marketing
            caption = self._make_authentic(caption)
        
        # Ajuste emoji usage
        if spec.emoji_usage == "low":
            # Réduit emojis (LinkedIn)
            caption = self._reduce_emojis(caption)
        
        elif spec.emoji_usage == "high":
            # Assure emojis présents (Twitter, IG)
            if style_profile and style_profile.get("emoji_frequency") == "high":
                # Déjà bon
                pass
        
        # Ajuste caption style
        if spec.caption_style == "short_punchy":
            # Twitter, Bluesky - court et percutant
            caption = self._make_punchy(caption)
        
        elif spec.caption_style == "storytelling":
            # Instagram, Facebook - peut être plus long, narratif
            # Garde comme est si déjà bon
            pass
        
        elif spec.caption_style == "informative":
            # LinkedIn - informatif, éducatif
            caption = self._make_informative(caption)
        
        return caption
    
    def _make_professional(self, text: str) -> str:
        """Rend texte plus professionnel pour LinkedIn"""
        
        # Replace casual words
        replacements = {
            "yo": "Bonjour",
            "les gars": "collègues",
            "check": "découvrez",
            "kiff": "apprécie",
            "insane": "impressionnant",
            "fou": "remarquable"
        }
        
        text_lower = text.lower()
        for casual, formal in replacements.items():
            text = re.sub(rf'\b{casual}\b', formal, text, flags=re.IGNORECASE)
        
        return text
    
    def _make_authentic(self, text: str) -> str:
        """Rend texte plus authentique pour Bluesky"""
        
        # Remove overly marketing phrases
        marketing_phrases = [
            "clique ici maintenant",
            "offre limitée",
            "ne rate pas",
            "inscris-toi maintenant"
        ]
        
        for phrase in marketing_phrases:
            text = text.replace(phrase, "")
        
        return text.strip()
    
    def _reduce_emojis(self, text: str) -> str:
        """Réduit nombre d'emojis pour LinkedIn"""
        
        # Pattern emoji
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            "]+", flags=re.UNICODE)
        
        emojis = emoji_pattern.findall(text)
        
        # Keep max 2-3 emojis
        if len(emojis) > 3:
            # Remove extra emojis
            for emoji in emojis[3:]:
                text = text.replace(emoji, "", 1)
        
        return text
    
    def _make_punchy(self, text: str) -> str:
        """Rend texte court et percutant pour Twitter/Bluesky"""
        
        # Split into sentences
        sentences = re.split(r'[.!?\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Keep first 2-3 sentences si trop long
        if len(text) > 200 and len(sentences) > 3:
            text = ". ".join(sentences[:3]) + "."
        
        return text
    
    def _make_informative(self, text: str) -> str:
        """Rend texte plus informatif pour LinkedIn"""
        
        # Ajoute context si manque
        if not any(word in text.lower() for word in ["pourquoi", "comment", "découvrez", "apprenez"]):
            # Ajoute hook informatif
            text = f"Découvrez comment {text}"
        
        return text
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extrait hashtags du texte"""
        return re.findall(r'#\w+', text)
    
    def _add_cta(self, caption: str, platform: Platform, spec: PlatformSpec) -> str:
        """Ajoute CTA approprié si manquant"""
        
        # Check si déjà CTA
        cta_indicators = ["👇", "🔗", "regarde", "clique", "check", "découvr"]
        has_cta = any(indicator in caption.lower() for indicator in cta_indicators)
        
        if not has_cta:
            # Ajoute CTA selon platform
            ctas = self.cta_templates.get(platform, [])
            if ctas:
                cta = ctas[0]
                caption = f"{caption}\n\n{cta}"
        
        return caption
    
    def _truncate_caption(self, text: str, max_length: int) -> str:
        """Truncate caption intelligemment"""
        
        if len(text) <= max_length:
            return text
        
        # Truncate at sentence boundary si possible
        truncated = text[:max_length-3]
        
        # Find last sentence end
        last_period = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_period > max_length * 0.7:
            return truncated[:last_period+1]
        
        # Sinon truncate avec ...
        return truncated + "..."
    
    def _calculate_optimization_score(
        self,
        caption: str,
        hashtags: List[str],
        spec: PlatformSpec,
        video_duration: Optional[int]
    ) -> float:
        """
        Calcule score d'optimisation (0-1)
        Mesure compliance avec platform specs
        """
        
        score = 0.0
        checks = 0
        
        # Check 1: Caption length optimal
        if spec.optimal_text_length * 0.8 <= len(caption) <= spec.optimal_text_length * 1.2:
            score += 0.25
        checks += 1
        
        # Check 2: Hashtag count optimal
        if spec.supports_hashtags:
            optimal_hashtag_count = spec.max_hashtags // 2
            if abs(len(hashtags) - optimal_hashtag_count) <= 2:
                score += 0.2
        else:
            if len(hashtags) == 0:
                score += 0.2
        checks += 1
        
        # Check 3: Video duration optimal
        if video_duration:
            if abs(video_duration - spec.optimal_video_duration) <= 15:
                score += 0.25
        else:
            score += 0.1  # Partial credit
        checks += 1
        
        # Check 4: Has CTA
        cta_indicators = ["👇", "🔗", "regarde", "clique", "check"]
        if any(ind in caption.lower() for ind in cta_indicators):
            score += 0.15
        checks += 1
        
        # Check 5: Emoji usage matches spec
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            "]+", flags=re.UNICODE)
        
        emoji_count = len(emoji_pattern.findall(caption))
        
        if spec.emoji_usage == "high" and emoji_count >= 2:
            score += 0.15
        elif spec.emoji_usage == "medium" and 1 <= emoji_count <= 3:
            score += 0.15
        elif spec.emoji_usage == "low" and emoji_count <= 2:
            score += 0.15
        checks += 1
        
        return min(1.0, score)
    
    def _estimate_engagement(
        self,
        platform: Platform,
        optimization_score: float,
        hashtag_count: int
    ) -> float:
        """Estime engagement basé sur optimization"""
        
        base_score = 5.0
        
        # Bonus optimization
        base_score += optimization_score * 3.0
        
        # Bonus hashtags (si platform les supporte)
        spec = self.specs[platform]
        if spec.supports_hashtags and hashtag_count > 0:
            base_score += min(hashtag_count * 0.3, 1.5)
        
        return min(10.0, base_score)
    
    def _generate_recommendations(
        self,
        caption: str,
        hashtags: List[str],
        spec: PlatformSpec,
        video_duration: Optional[int],
        optimization_score: float
    ) -> List[str]:
        """Génère recommandations d'amélioration"""
        
        recommendations = []
        
        # Caption length
        if len(caption) > spec.max_text_length * 0.9:
            recommendations.append(f"⚠️ Caption proche de la limite ({len(caption)}/{spec.max_text_length} chars)")
        
        if len(caption) < spec.optimal_text_length * 0.5:
            recommendations.append("💡 Caption un peu court - ajoute plus de context")
        
        # Hashtags
        if spec.supports_hashtags:
            if len(hashtags) == 0:
                recommendations.append(f"💡 Ajoute 2-{spec.max_hashtags} hashtags pour visibilité")
            elif len(hashtags) > spec.max_hashtags:
                recommendations.append(f"⚠️ Trop de hashtags ({len(hashtags)}/{spec.max_hashtags} max)")
        
        # Video duration
        if video_duration:
            if video_duration > spec.max_video_duration:
                recommendations.append(f"⚠️ Vidéo trop longue ({video_duration}s > {spec.max_video_duration}s max)")
            elif video_duration < spec.optimal_video_duration * 0.5:
                recommendations.append(f"💡 Vidéo courte ({video_duration}s) - optimal: {spec.optimal_video_duration}s")
        
        # Optimization score
        if optimization_score < 0.6:
            recommendations.append("📊 Score d'optimisation faible - vérifie recommendations ci-dessus")
        elif optimization_score >= 0.8:
            recommendations.append("✅ Excellent! Bien optimisé pour cette platform")
        
        # Platform-specific
        if spec.platform == "instagram" and spec.link_placement == "bio":
            recommendations.append("💡 Instagram: Mentionne 'lien dans bio' si applicable")
        
        if spec.platform == "linkedin" and spec.tone == "professional":
            recommendations.append("💡 LinkedIn: Garde tone professionnel et informatif")
        
        needs_captions = spec.platform in ["facebook", "linkedin"]
        if needs_captions:
            recommendations.append("📝 Ajoute sous-titres à la vidéo (best practice pour cette platform)")
        
        return recommendations
    
    def get_optimal_segment(
        self,
        video_duration: int,
        platform: Platform
    ) -> VideoSegment:
        """
        Retourne segment vidéo optimal pour platform
        
        Args:
            video_duration: Durée totale vidéo
            platform: Platform cible
            
        Returns:
            VideoSegment optimisé
        """
        
        spec = self.specs[platform]
        optimal_duration = spec.optimal_video_duration
        
        # Si vidéo plus courte que optimal, prend tout
        if video_duration <= optimal_duration:
            return VideoSegment(
                start_time=0,
                end_time=video_duration,
                duration=video_duration,
                aspect_ratio=spec.preferred_aspect_ratios[0],
                needs_captions=platform in [Platform.FACEBOOK, Platform.LINKEDIN],
                recommended_text_overlay="Hook accrocheur" if platform == Platform.INSTAGRAM else None
            )
        
        # Sinon, extrait segment optimal
        # Préfère début (hook) + climax
        start_time = 0
        end_time = optimal_duration
        
        return VideoSegment(
            start_time=start_time,
            end_time=end_time,
            duration=optimal_duration,
            aspect_ratio=spec.preferred_aspect_ratios[0],
            needs_captions=platform in [Platform.FACEBOOK, Platform.LINKEDIN],
            recommended_text_overlay="Hook accrocheur" if platform == Platform.INSTAGRAM else None
        )
    
    def batch_adapt(
        self,
        base_content: str,
        platforms: List[Platform],
        video_duration: Optional[int] = None,
        style_profile: Optional[Dict] = None,
        link: Optional[str] = None
    ) -> Dict[str, AdaptedContent]:
        """
        Adapte contenu pour plusieurs platforms simultanément
        
        Returns:
            Dict {platform: AdaptedContent}
        """
        
        results = {}
        
        for platform in platforms:
            adapted = self.adapt_content(
                base_content=base_content,
                platform=platform,
                video_duration=video_duration,
                style_profile=style_profile,
                link=link
            )
            results[platform.value] = adapted
        
        return results


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """Test du Platform Adapter"""
    
    print("🎨 Platform Adapter - Test")
    print("=" * 70)
    
    # Initialize
    adapter = PlatformAdapter()
    
    # Base content (généré par Style Learner)
    base_content = """🔥 OK LES GARS

J'ai passé 5h sur ce projet de montage vidéo insane

Le résultat? INCROYABLE 💯

Check la vidéo complète 👇

#tutorial #editing #insane"""
    
    print(f"\n📝 Base content:")
    print("=" * 70)
    print(base_content)
    print("=" * 70)
    
    # Test 1: Adapt pour Twitter
    print("\n\n1️⃣ Adaptation pour TWITTER...")
    twitter_adapted = adapter.adapt_content(
        base_content=base_content,
        platform=Platform.TWITTER,
        video_duration=35,
        link="https://only.com/video/123"
    )
    
    print(f"\n✅ Twitter adapted:")
    print(f"  Caption ({twitter_adapted.caption_length} chars):")
    print(f"  {twitter_adapted.caption}")
    print(f"\n  Hashtags ({twitter_adapted.hashtag_count}): {twitter_adapted.hashtags}")
    print(f"  Video: {twitter_adapted.video_duration}s, {twitter_adapted.aspect_ratio}")
    print(f"  Optimization: {twitter_adapted.optimization_score:.0%}")
    print(f"  Estimated engagement: {twitter_adapted.estimated_engagement:.1f}/10")
    if twitter_adapted.recommendations:
        print(f"\n  📊 Recommendations:")
        for rec in twitter_adapted.recommendations:
            print(f"    {rec}")
    
    # Test 2: Adapt pour LinkedIn
    print("\n\n2️⃣ Adaptation pour LINKEDIN...")
    linkedin_adapted = adapter.adapt_content(
        base_content=base_content,
        platform=Platform.LINKEDIN,
        video_duration=50,
        link="https://only.com/video/123"
    )
    
    print(f"\n✅ LinkedIn adapted:")
    print(f"  Caption ({linkedin_adapted.caption_length} chars):")
    print(f"  {linkedin_adapted.caption}")
    print(f"\n  Hashtags ({linkedin_adapted.hashtag_count}): {linkedin_adapted.hashtags}")
    print(f"  Video: {linkedin_adapted.video_duration}s, {linkedin_adapted.aspect_ratio}")
    print(f"  Needs captions: {linkedin_adapted.needs_captions}")
    print(f"  Optimization: {linkedin_adapted.optimization_score:.0%}")
    if linkedin_adapted.recommendations:
        print(f"\n  📊 Recommendations:")
        for rec in linkedin_adapted.recommendations:
            print(f"    {rec}")
    
    # Test 3: Batch adapt pour toutes platforms
    print("\n\n3️⃣ Batch adaptation (toutes platforms)...")
    
    all_platforms = [Platform.TWITTER, Platform.INSTAGRAM, Platform.FACEBOOK, 
                     Platform.LINKEDIN, Platform.BLUESKY]
    
    batch_results = adapter.batch_adapt(
        base_content=base_content,
        platforms=all_platforms,
        video_duration=45,
        link="https://only.com/video/123"
    )
    
    print(f"\n✅ Batch results ({len(batch_results)} platforms):")
    for platform_name, adapted in batch_results.items():
        print(f"\n  {platform_name.upper()}:")
        print(f"    Length: {adapted.caption_length} chars")
        print(f"    Hashtags: {adapted.hashtag_count}")
        print(f"    Optimization: {adapted.optimization_score:.0%}")
        print(f"    Engagement: {adapted.estimated_engagement:.1f}/10")
    
    print("\n" + "=" * 70)
    print("✅ Platform Adapter tests completed!")
