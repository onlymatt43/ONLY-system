"""
Video Content Analyzer - Analyse vidéos pour marketing optimal
Détecte hooks, climax, segments preview, platform fit scores
"""

import os
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import statistics


# ==================== DATA MODELS ====================

@dataclass
class VideoInsights:
    """Résultats analyse complète d'une vidéo"""
    video_id: str
    video_guid: str
    
    # Métadonnées techniques
    duration_seconds: int
    resolution: str
    thumbnail_url: str
    thumbnail_quality_score: float  # 0-1
    
    # Analyse contenu
    content_type: str  # tutorial, vlog, review, teaser, entertainment
    energy_level: str  # low, medium, high
    
    # Timestamps clés (en secondes)
    hook_timestamp: int  # Moment où ça devient intéressant
    climax_timestamp: Optional[int]  # Moment le plus intense
    
    # Segments preview recommandés
    best_preview_segments: List[Dict[str, Any]]
    
    # Marketing insights
    engagement_score: float  # 0-10
    viral_potential: float  # 0-10
    platform_fit: Dict[str, float]  # score par plateforme 0-10
    
    # Hooks suggérés
    suggested_hooks: List[str]
    
    # CTA recommendations
    best_cta_timing: str  # start, middle, end
    cta_type: str  # curiosity, urgency, value
    
    # Métadonnées
    analyzed_at: float


# ==================== VIDEO ANALYZER ====================

class VideoAnalyzer:
    """Analyse vidéos Bunny Stream pour insights marketing"""
    
    def __init__(self, curator_url: str = "http://localhost:5061"):
        self.curator_url = curator_url
        
        # Seuils pour classification
        self.short_video = 60  # < 1 min
        self.medium_video = 300  # 1-5 min
        self.long_video = 600  # 5-10 min
        
        # Platform preferences
        self.platform_preferences = {
            "twitter": {
                "ideal_duration": 30,  # secondes
                "max_duration": 140,
                "format_preference": "square",  # ou vertical
                "energy_boost": 1.2  # préfère high energy
            },
            "instagram": {
                "ideal_duration": 60,
                "max_duration": 90,
                "format_preference": "vertical",  # 9:16
                "energy_boost": 1.3
            },
            "facebook": {
                "ideal_duration": 90,
                "max_duration": 180,
                "format_preference": "horizontal",
                "energy_boost": 1.0
            },
            "linkedin": {
                "ideal_duration": 45,
                "max_duration": 90,
                "format_preference": "square",
                "energy_boost": 0.8  # préfère medium energy, pro
            },
            "bluesky": {
                "ideal_duration": 45,
                "max_duration": 120,
                "format_preference": "any",
                "energy_boost": 1.1
            }
        }
    
    def analyze_video(self, video_id: str) -> VideoInsights:
        """
        Analyse complète d'une vidéo depuis Curator Bot
        
        Args:
            video_id: ID vidéo dans Curator database
            
        Returns:
            VideoInsights avec toutes les données d'analyse
        """
        
        # 1. Récupère données vidéo depuis Curator
        video_data = self._fetch_video_from_curator(video_id)
        
        if not video_data:
            raise ValueError(f"Video {video_id} not found in Curator")
        
        # 2. Analyse métadonnées techniques
        tech_analysis = self._analyze_technical_metadata(video_data)
        
        # 3. Détecte type de contenu et energy level
        content_analysis = self._analyze_content_type(video_data, tech_analysis)
        
        # 4. Identifie timestamps clés
        timestamps = self._identify_key_timestamps(video_data, tech_analysis)
        
        # 5. Génère segments preview recommandés
        preview_segments = self._generate_preview_segments(
            video_data, 
            tech_analysis, 
            timestamps
        )
        
        # 6. Calcule scores marketing
        marketing_scores = self._calculate_marketing_scores(
            video_data,
            tech_analysis,
            content_analysis
        )
        
        # 7. Génère hooks suggérés
        hooks = self._generate_suggested_hooks(
            video_data,
            content_analysis,
            marketing_scores
        )
        
        # 8. Recommande CTA strategy
        cta_strategy = self._recommend_cta_strategy(
            tech_analysis,
            content_analysis,
            timestamps
        )
        
        # 9. Compile tout
        insights = VideoInsights(
            video_id=video_id,
            video_guid=video_data.get('bunny_guid', ''),
            duration_seconds=tech_analysis['duration'],
            resolution=tech_analysis['resolution'],
            thumbnail_url=tech_analysis['thumbnail_url'],
            thumbnail_quality_score=tech_analysis['thumbnail_quality'],
            content_type=content_analysis['type'],
            energy_level=content_analysis['energy'],
            hook_timestamp=timestamps['hook'],
            climax_timestamp=timestamps.get('climax'),
            best_preview_segments=preview_segments,
            engagement_score=marketing_scores['engagement'],
            viral_potential=marketing_scores['viral_potential'],
            platform_fit=marketing_scores['platform_fit'],
            suggested_hooks=hooks,
            best_cta_timing=cta_strategy['timing'],
            cta_type=cta_strategy['type'],
            analyzed_at=time.time()
        )
        
        return insights
    
    def _fetch_video_from_curator(self, video_id: str) -> Optional[Dict]:
        """Récupère données vidéo depuis Curator Bot API"""
        try:
            url = f"{self.curator_url}/videos/{video_id}"
            r = requests.get(url, timeout=5)
            
            if r.status_code == 200:
                return r.json()
            else:
                print(f"[VideoAnalyzer] Failed to fetch video {video_id}: {r.status_code}")
                return None
                
        except Exception as e:
            print(f"[VideoAnalyzer] Error fetching video: {e}")
            return None
    
    def _analyze_technical_metadata(self, video_data: Dict) -> Dict:
        """Analyse métadonnées techniques"""
        
        # Duration peut être 'duration' ou 'length' selon source
        duration = video_data.get('duration') or video_data.get('length', 0)
        
        # Extraire width/height depuis bunny_data si disponible
        import json
        bunny_data_str = video_data.get('bunny_data', '{}')
        try:
            bunny_data = json.loads(bunny_data_str) if isinstance(bunny_data_str, str) else bunny_data_str
            width = bunny_data.get('width', 1920)
            height = bunny_data.get('height', 1080)
        except:
            width = 1920
            height = 1080
        
        thumbnail_url = video_data.get('thumbnail_url', '')
        
        # Calcule résolution
        if width >= 3840:
            resolution = "4K"
        elif width >= 1920:
            resolution = "1080p"
        elif width >= 1280:
            resolution = "720p"
        else:
            resolution = "SD"
        
        # Score qualité thumbnail (basique, peut être amélioré avec image analysis)
        thumbnail_quality = 0.8 if thumbnail_url else 0.3
        
        return {
            "duration": duration,
            "resolution": resolution,
            "width": width,
            "height": height,
            "thumbnail_url": thumbnail_url,
            "thumbnail_quality": thumbnail_quality,
            "aspect_ratio": width / height if height > 0 else 1.78
        }
    
    def _analyze_content_type(self, video_data: Dict, tech: Dict) -> Dict:
        """Détecte type de contenu et energy level"""
        
        title = video_data.get('title', '').lower()
        duration = tech['duration']
        
        # Détection type de contenu (règles basiques, peut être amélioré avec NLP)
        content_type = "entertainment"  # default
        
        if any(word in title for word in ["tutorial", "how to", "guide", "learn"]):
            content_type = "tutorial"
        elif any(word in title for word in ["review", "test", "comparison"]):
            content_type = "review"
        elif any(word in title for word in ["vlog", "day in", "behind"]):
            content_type = "vlog"
        elif duration < 60:
            content_type = "teaser"
        
        # Détection energy level (heuristique basique)
        energy = "medium"  # default
        
        # Courtes vidéos = généralement high energy
        if duration < 90:
            energy = "high"
        # Longues vidéos = souvent low/medium energy
        elif duration > 600:
            energy = "low"
        
        # Détection via titre (emojis, caps, exclamations)
        title_original = video_data.get('title', '')
        emoji_count = sum(1 for char in title_original if ord(char) > 127)
        caps_ratio = sum(1 for c in title_original if c.isupper()) / max(len(title_original), 1)
        exclamations = title_original.count('!')
        
        if emoji_count >= 2 or caps_ratio > 0.3 or exclamations >= 2:
            energy = "high"
        
        return {
            "type": content_type,
            "energy": energy,
            "emoji_count": emoji_count,
            "caps_ratio": caps_ratio
        }
    
    def _identify_key_timestamps(self, video_data: Dict, tech: Dict) -> Dict:
        """Identifie timestamps clés (hook, climax)"""
        
        duration = tech['duration']
        
        # Hook timestamp (début intéressant)
        # Règle: premiers 3-5 secondes pour hook attention
        hook = min(3, duration)
        
        # Climax timestamp (moment le plus intense)
        # Heuristique: généralement vers 60-70% de la vidéo
        climax = None
        if duration > 60:
            climax = int(duration * 0.65)
        
        return {
            "hook": hook,
            "climax": climax
        }
    
    def _generate_preview_segments(
        self, 
        video_data: Dict, 
        tech: Dict,
        timestamps: Dict
    ) -> List[Dict[str, Any]]:
        """Génère segments preview recommandés pour chaque plateforme"""
        
        duration = tech['duration']
        segments = []
        
        # Segment 1: Hook fort (début)
        segments.append({
            "start": 0,
            "end": min(30, duration),
            "duration": min(30, duration),
            "reason": "strong_hook",
            "platforms": ["twitter", "instagram", "linkedin"],
            "description": "Début accrocheur avec hook fort"
        })
        
        # Segment 2: Peak action (milieu)
        if duration > 90 and timestamps.get('climax'):
            climax = timestamps['climax']
            segments.append({
                "start": max(0, climax - 15),
                "end": min(duration, climax + 15),
                "duration": 30,
                "reason": "action_peak",
                "platforms": ["instagram", "facebook"],
                "description": "Moment le plus intense/intéressant"
            })
        
        # Segment 3: Cliffhanger (fin)
        if duration > 60:
            segments.append({
                "start": max(0, duration - 30),
                "end": duration,
                "duration": min(30, duration),
                "reason": "cliffhanger",
                "platforms": ["twitter", "bluesky"],
                "description": "Fin qui donne envie de voir la suite"
            })
        
        # Segment 4: Extended preview (Facebook/LinkedIn)
        if duration > 120:
            segments.append({
                "start": 0,
                "end": 90,
                "duration": 90,
                "reason": "extended_preview",
                "platforms": ["facebook", "linkedin"],
                "description": "Preview long pour contexte complet"
            })
        
        return segments
    
    def _calculate_marketing_scores(
        self,
        video_data: Dict,
        tech: Dict,
        content: Dict
    ) -> Dict:
        """Calcule scores marketing (engagement, viral, platform fit)"""
        
        duration = tech['duration']
        energy = content['energy']
        content_type = content['type']
        
        # Engagement score (0-10)
        engagement = 5.0  # baseline
        
        # Boost si bonne durée (60-300s optimal)
        if 60 <= duration <= 300:
            engagement += 2.0
        elif duration < 30 or duration > 600:
            engagement -= 1.0
        
        # Boost si high energy
        if energy == "high":
            engagement += 1.5
        elif energy == "low":
            engagement -= 0.5
        
        # Boost si bonne qualité thumbnail
        if tech['thumbnail_quality'] > 0.7:
            engagement += 1.0
        
        # Boost si titre engageant
        if content['emoji_count'] >= 2:
            engagement += 0.5
        
        engagement = max(0, min(10, engagement))
        
        # Viral potential (0-10)
        viral = 4.0  # baseline
        
        # Courtes vidéos = plus viral
        if duration < 60:
            viral += 3.0
        elif duration < 120:
            viral += 1.5
        
        # High energy = plus viral
        if energy == "high":
            viral += 2.0
        
        # Certains types plus viraux
        if content_type in ["teaser", "entertainment"]:
            viral += 1.0
        
        viral = max(0, min(10, viral))
        
        # Platform fit scores
        platform_fit = {}
        
        for platform, prefs in self.platform_preferences.items():
            score = 5.0  # baseline
            
            # Score basé sur durée
            ideal_dur = prefs['ideal_duration']
            max_dur = prefs['max_duration']
            
            if duration <= ideal_dur:
                score += 3.0
            elif duration <= max_dur:
                score += 1.5
            else:
                # Pénalité si trop long
                overage = (duration - max_dur) / max_dur
                score -= min(3.0, overage * 2)
            
            # Score basé sur energy
            energy_boost = prefs['energy_boost']
            if energy == "high":
                score += (energy_boost - 1.0) * 2
            elif energy == "low":
                score -= (energy_boost - 1.0) * 2
            
            # Score basé sur aspect ratio (simplifié)
            aspect = tech['aspect_ratio']
            if prefs['format_preference'] == "vertical" and aspect < 1.0:
                score += 1.0
            elif prefs['format_preference'] == "horizontal" and aspect > 1.5:
                score += 1.0
            elif prefs['format_preference'] == "square" and 0.9 <= aspect <= 1.1:
                score += 1.0
            
            platform_fit[platform] = max(0, min(10, score))
        
        return {
            "engagement": round(engagement, 1),
            "viral_potential": round(viral, 1),
            "platform_fit": {k: round(v, 1) for k, v in platform_fit.items()}
        }
    
    def _generate_suggested_hooks(
        self,
        video_data: Dict,
        content: Dict,
        scores: Dict
    ) -> List[str]:
        """Génère hooks/titres suggérés"""
        
        title = video_data.get('title', 'Cette vidéo')
        content_type = content['type']
        energy = content['energy']
        
        hooks = []
        
        # Templates par type de contenu
        if content_type == "tutorial":
            hooks.extend([
                f"🎯 Comment faire comme dans '{title}'",
                f"💡 La technique que PERSONNE ne connaît",
                f"⚡ {title} - Résultats en 5 minutes"
            ])
        
        elif content_type == "review":
            hooks.extend([
                f"😱 J'ai testé {title} - CHOQUANT",
                f"🔥 La vérité sur {title}",
                f"💎 {title} - Ça vaut vraiment le coup?"
            ])
        
        elif content_type == "teaser":
            hooks.extend([
                f"👀 Tu n'es PAS prêt pour ça...",
                f"🤯 Attends de voir la fin",
                f"⏰ Drop dans 24h - Prépare-toi"
            ])
        
        else:  # entertainment, vlog
            hooks.extend([
                f"🔥 {title} - C'est INSANE",
                f"😂 Tu dois voir ça MAINTENANT",
                f"💯 {title} - Meilleur moment ever"
            ])
        
        # Hooks basés sur viral potential
        if scores['viral_potential'] >= 7.0:
            hooks.append(f"🚀 Ça va devenir VIRAL - {title}")
        
        # Limite à 5 hooks max
        return hooks[:5]
    
    def _recommend_cta_strategy(
        self,
        tech: Dict,
        content: Dict,
        timestamps: Dict
    ) -> Dict:
        """Recommande stratégie CTA (timing, type)"""
        
        duration = tech['duration']
        content_type = content['type']
        
        # Timing du CTA
        if duration < 60:
            # Courte vidéo: CTA à la fin
            timing = "end"
        elif content_type == "tutorial":
            # Tutorial: CTA au milieu (après avoir montré value)
            timing = "middle"
        else:
            # Default: CTA à la fin
            timing = "end"
        
        # Type de CTA
        if content_type in ["teaser", "entertainment"]:
            cta_type = "curiosity"  # "Veux-tu voir la suite?"
        elif content_type == "tutorial":
            cta_type = "value"  # "Accède au guide complet"
        else:
            cta_type = "urgency"  # "Regarde maintenant avant que ça disparaisse"
        
        return {
            "timing": timing,
            "type": cta_type
        }
    
    def get_optimal_preview_for_platform(
        self,
        insights: VideoInsights,
        platform: str
    ) -> Optional[Dict]:
        """
        Retourne le meilleur segment preview pour une plateforme
        
        Args:
            insights: VideoInsights de analyze_video()
            platform: twitter, instagram, facebook, linkedin, bluesky
            
        Returns:
            Dict avec start, end, duration ou None
        """
        
        # Filtre segments par plateforme
        matching_segments = [
            seg for seg in insights.best_preview_segments
            if platform in seg['platforms']
        ]
        
        if not matching_segments:
            # Fallback: premier segment
            return insights.best_preview_segments[0] if insights.best_preview_segments else None
        
        # Retourne segment avec durée la plus proche de l'idéal
        ideal_duration = self.platform_preferences[platform]['ideal_duration']
        
        best_segment = min(
            matching_segments,
            key=lambda seg: abs(seg['duration'] - ideal_duration)
        )
        
        return best_segment


# ==================== BATCH ANALYZER ====================

class BatchVideoAnalyzer:
    """Analyse multiple vidéos en batch"""
    
    def __init__(self, analyzer: VideoAnalyzer):
        self.analyzer = analyzer
    
    def analyze_library(
        self,
        library_type: str = "all",
        limit: Optional[int] = None
    ) -> List[VideoInsights]:
        """
        Analyse toutes les vidéos d'une library
        
        Args:
            library_type: "public", "private", ou "all"
            limit: Nombre max de vidéos à analyser
            
        Returns:
            Liste de VideoInsights
        """
        
        # Récupère vidéos depuis Curator
        curator_url = self.analyzer.curator_url
        params = {}
        
        if library_type != "all":
            params['library'] = library_type
        if limit:
            params['limit'] = limit
        
        try:
            r = requests.get(f"{curator_url}/videos", params=params, timeout=10)
            
            if r.status_code != 200:
                print(f"[BatchAnalyzer] Failed to fetch videos: {r.status_code}")
                return []
            
            videos = r.json()
            
        except Exception as e:
            print(f"[BatchAnalyzer] Error fetching videos: {e}")
            return []
        
        # Analyse chaque vidéo
        insights_list = []
        
        for video in videos:
            video_id = video.get('id')
            
            if not video_id:
                continue
            
            try:
                insights = self.analyzer.analyze_video(str(video_id))
                insights_list.append(insights)
                print(f"[BatchAnalyzer] ✅ Analyzed video {video_id}")
                
            except Exception as e:
                print(f"[BatchAnalyzer] ❌ Failed to analyze {video_id}: {e}")
        
        return insights_list
    
    def get_top_performers(
        self,
        insights_list: List[VideoInsights],
        metric: str = "engagement",
        limit: int = 10
    ) -> List[VideoInsights]:
        """
        Retourne top N vidéos par métrique
        
        Args:
            insights_list: Liste VideoInsights
            metric: "engagement", "viral_potential", ou platform name
            limit: Nombre de résultats
            
        Returns:
            Liste VideoInsights triée
        """
        
        if metric == "engagement":
            sorted_insights = sorted(
                insights_list,
                key=lambda x: x.engagement_score,
                reverse=True
            )
        elif metric == "viral_potential":
            sorted_insights = sorted(
                insights_list,
                key=lambda x: x.viral_potential,
                reverse=True
            )
        elif metric in ["twitter", "instagram", "facebook", "linkedin", "bluesky"]:
            sorted_insights = sorted(
                insights_list,
                key=lambda x: x.platform_fit.get(metric, 0),
                reverse=True
            )
        else:
            return insights_list[:limit]
        
        return sorted_insights[:limit]


if __name__ == "__main__":
    """Test du Video Analyzer"""
    
    print("🎥 Video Analyzer - Test")
    print("=" * 50)
    
    # Initialise analyzer
    analyzer = VideoAnalyzer(curator_url="http://localhost:5061")
    
    # Test: analyse première vidéo
    try:
        r = requests.get("http://localhost:5061/videos?limit=1", timeout=5)
        
        if r.status_code == 200:
            videos = r.json()
            
            if videos:
                video_id = videos[0]['id']
                print(f"\n📊 Analyse vidéo ID: {video_id}")
                print(f"Titre: {videos[0].get('title', 'N/A')}")
                
                insights = analyzer.analyze_video(str(video_id))
                
                print(f"\n✅ Analyse complétée!")
                print(f"\n📈 Scores:")
                print(f"  Engagement: {insights.engagement_score}/10")
                print(f"  Viral Potential: {insights.viral_potential}/10")
                print(f"\n🌐 Platform Fit:")
                for platform, score in insights.platform_fit.items():
                    print(f"  {platform.capitalize()}: {score}/10")
                
                print(f"\n🎯 Hooks suggérés:")
                for i, hook in enumerate(insights.suggested_hooks, 1):
                    print(f"  {i}. {hook}")
                
                print(f"\n🎬 Preview Segments:")
                for seg in insights.best_preview_segments:
                    print(f"  [{seg['start']}s - {seg['end']}s] ({seg['duration']}s)")
                    print(f"    Raison: {seg['reason']}")
                    print(f"    Platforms: {', '.join(seg['platforms'])}")
                
            else:
                print("❌ Aucune vidéo trouvée dans Curator")
        else:
            print(f"❌ Curator non accessible (HTTP {r.status_code})")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n💡 Assure-toi que Curator Bot tourne sur port 5061")
