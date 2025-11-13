"""
Blog & Homepage Engine - Phase 2 Module 3/3
Auto-génération blog posts, SEO, dynamic homepage
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import sqlite3
import json
import re


class ContentType(Enum):
    """Types de contenu"""
    BLOG_POST = "blog_post"
    HOMEPAGE_SECTION = "homepage_section"
    CATEGORY_PAGE = "category_page"
    LANDING_PAGE = "landing_page"


class SEOPriority(Enum):
    """Priorité SEO"""
    HIGH = "high"  # Articles principaux
    MEDIUM = "medium"  # Articles secondaires
    LOW = "low"  # Pages support


@dataclass
class BlogPost:
    """Article de blog"""
    id: Optional[int] = None
    video_id: str = ""
    title: str = ""
    slug: str = ""
    intro: str = ""
    body: str = ""
    conclusion: str = ""
    meta_description: str = ""
    keywords: List[str] = field(default_factory=list)
    category: str = "tutorial"
    author: str = "Matt"
    read_time_minutes: int = 5
    seo_score: float = 0.0
    published: bool = False
    published_at: Optional[datetime] = None
    view_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class HomepageSection:
    """Section de homepage"""
    id: Optional[int] = None
    section_type: str = "trending"  # trending, latest, popular, category
    title: str = ""
    subtitle: str = ""
    video_ids: List[str] = field(default_factory=list)
    display_order: int = 0
    is_active: bool = True
    auto_update: bool = True  # Se met à jour automatiquement
    update_frequency_hours: int = 24


@dataclass
class SEOMetadata:
    """Métadonnées SEO"""
    title: str = ""
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    canonical_url: str = ""
    schema_markup: Dict[str, Any] = field(default_factory=dict)


class BlogEngine:
    """
    Moteur de blog et homepage
    Auto-génération posts, SEO, sections dynamiques
    """
    
    def __init__(self, db_path: str = "blog_engine.db"):
        self.db_path = db_path
        self._init_database()
        
        # Templates de structure blog
        self.blog_templates = {
            "tutorial": {
                "intro_pattern": "Dans cette vidéo, je te montre {skill} en {duration}.\n\n{hook}",
                "sections": ["Ce que tu vas apprendre", "Techniques utilisées", "Résultats attendus"],
                "cta": "Regarde la vidéo complète pour voir toutes les étapes en détail!"
            },
            "showcase": {
                "intro_pattern": "Check ce projet {project_type} que j'ai réalisé. {wow_factor}",
                "sections": ["Le concept", "Le processus", "Les défis"],
                "cta": "Découvre toutes les coulisses dans la vidéo!"
            },
            "tips": {
                "intro_pattern": "{tip_count} astuces pour {goal}. Tu vas kiffer!",
                "sections": ["Astuce #1", "Astuce #2", "Astuce #3"],
                "cta": "Plus de techniques dans la vidéo complète!"
            }
        }
    
    def _init_database(self):
        """Initialise base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table blog posts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                intro TEXT,
                body TEXT,
                conclusion TEXT,
                meta_description TEXT,
                keywords TEXT,
                category TEXT DEFAULT 'tutorial',
                author TEXT DEFAULT 'Matt',
                read_time_minutes INTEGER DEFAULT 5,
                seo_score REAL DEFAULT 0.0,
                published INTEGER DEFAULT 0,
                published_at TEXT,
                view_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table homepage sections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS homepage_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_type TEXT NOT NULL,
                title TEXT NOT NULL,
                subtitle TEXT,
                video_ids TEXT,
                display_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                auto_update INTEGER DEFAULT 1,
                update_frequency_hours INTEGER DEFAULT 24,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table SEO metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seo_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_type TEXT NOT NULL,
                page_id TEXT NOT NULL,
                title TEXT,
                description TEXT,
                keywords TEXT,
                og_title TEXT,
                og_description TEXT,
                og_image TEXT,
                canonical_url TEXT,
                schema_markup TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(page_type, page_id)
            )
        """)
        
        # Table analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                content_id TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                time_on_page_seconds INTEGER DEFAULT 0,
                bounce_rate REAL DEFAULT 0.0,
                conversions INTEGER DEFAULT 0,
                date TEXT DEFAULT CURRENT_DATE,
                UNIQUE(content_type, content_id, date)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # === BLOG GENERATION ===
    
    def generate_blog_post(
        self,
        video_id: str,
        video_title: str,
        video_description: str,
        category: str = "tutorial",
        keywords: Optional[List[str]] = None
    ) -> BlogPost:
        """Génère article de blog à partir d'une vidéo"""
        
        # Créer slug
        slug = self._create_slug(video_title)
        
        # Extract keywords si pas fournis
        if not keywords:
            keywords = self._extract_keywords(video_title + " " + video_description)
        
        # Choisir template
        template = self.blog_templates.get(category, self.blog_templates["tutorial"])
        
        # Générer intro
        intro = self._generate_intro(video_title, video_description, template)
        
        # Générer body
        body = self._generate_body(video_description, template, keywords)
        
        # Générer conclusion
        conclusion = self._generate_conclusion(template)
        
        # Générer meta description
        meta_description = self._generate_meta_description(video_title, keywords)
        
        # Calculer read time
        word_count = len(intro.split()) + len(body.split()) + len(conclusion.split())
        read_time = max(1, word_count // 200)  # 200 mots/min
        
        # Créer post
        post = BlogPost(
            video_id=video_id,
            title=video_title,
            slug=slug,
            intro=intro,
            body=body,
            conclusion=conclusion,
            meta_description=meta_description,
            keywords=keywords,
            category=category,
            read_time_minutes=read_time
        )
        
        # Calculer SEO score
        post.seo_score = self._calculate_seo_score(post)
        
        # Sauvegarder
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO blog_posts (
                video_id, title, slug, intro, body, conclusion,
                meta_description, keywords, category, read_time_minutes,
                seo_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post.video_id,
            post.title,
            post.slug,
            post.intro,
            post.body,
            post.conclusion,
            post.meta_description,
            json.dumps(post.keywords),
            post.category,
            post.read_time_minutes,
            post.seo_score
        ))
        
        post.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return post
    
    def _create_slug(self, title: str) -> str:
        """Crée slug URL-friendly"""
        slug = title.lower()
        slug = re.sub(r'[àáâãäå]', 'a', slug)
        slug = re.sub(r'[èéêë]', 'e', slug)
        slug = re.sub(r'[ìíîï]', 'i', slug)
        slug = re.sub(r'[òóôõö]', 'o', slug)
        slug = re.sub(r'[ùúûü]', 'u', slug)
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]  # Max 100 chars
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords du texte"""
        # Mots communs à ignorer
        stop_words = {"le", "la", "les", "un", "une", "des", "de", "du", "en", "et", "à", "pour", "dans", "sur"}
        
        words = re.findall(r'\b\w{4,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        # Count fréquence
        from collections import Counter
        word_freq = Counter(keywords)
        
        # Top 5 mots
        return [word for word, count in word_freq.most_common(5)]
    
    def _generate_intro(self, title: str, description: str, template: Dict) -> str:
        """Génère introduction"""
        # Extract info du description
        duration = "quelques minutes"
        if "10 min" in description or "10min" in description:
            duration = "10 minutes"
        elif "5 min" in description:
            duration = "5 minutes"
        
        hook = description[:200] if len(description) > 200 else description
        
        intro = f"""🎬 {title}

{hook}

Dans cette vidéo, je te montre toutes les techniques et astuces pour maîtriser ce sujet en {duration}. C'est du concret, pas de blabla!

"""
        return intro
    
    def _generate_body(self, description: str, template: Dict, keywords: List[str]) -> str:
        """Génère corps de l'article"""
        sections = template.get("sections", ["Contenu", "Techniques", "Résultats"])
        
        body = ""
        for i, section_title in enumerate(sections, 1):
            body += f"## {section_title}\n\n"
            
            if i == 1:
                body += f"{description}\n\n"
            elif i == 2:
                body += f"Les techniques couvertes incluent: {', '.join(keywords)}.\n\n"
            else:
                body += "Tu vas obtenir des résultats professionnels grâce à ces méthodes éprouvées.\n\n"
        
        return body
    
    def _generate_conclusion(self, template: Dict) -> str:
        """Génère conclusion"""
        cta = template.get("cta", "Regarde la vidéo complète!")
        
        conclusion = f"""## Prêt à passer au niveau supérieur?

{cta}

💡 N'oublie pas de t'abonner pour plus de contenu comme celui-ci!

🎯 Questions? Laisse un commentaire, je réponds à TOUT!
"""
        return conclusion
    
    def _generate_meta_description(self, title: str, keywords: List[str]) -> str:
        """Génère meta description SEO"""
        desc = f"{title}. Tutoriel complet"
        if keywords:
            desc += f" sur {', '.join(keywords[:3])}"
        desc += ". Guide pas-à-pas avec techniques pro!"
        return desc[:160]  # Google limit
    
    def _calculate_seo_score(self, post: BlogPost) -> float:
        """Calcule score SEO"""
        score = 0.0
        
        # Title length (50-60 chars optimal)
        if 50 <= len(post.title) <= 60:
            score += 2.0
        elif 30 <= len(post.title) <= 70:
            score += 1.0
        
        # Meta description (150-160 chars optimal)
        if 150 <= len(post.meta_description) <= 160:
            score += 2.0
        elif 120 <= len(post.meta_description) <= 170:
            score += 1.0
        
        # Keywords présents dans title
        title_lower = post.title.lower()
        keyword_in_title = sum(1 for kw in post.keywords if kw in title_lower)
        score += min(keyword_in_title * 1.0, 2.0)
        
        # Content length (300+ words)
        total_words = len(post.intro.split()) + len(post.body.split()) + len(post.conclusion.split())
        if total_words >= 500:
            score += 2.0
        elif total_words >= 300:
            score += 1.0
        
        # Keywords count (3-5 optimal)
        if 3 <= len(post.keywords) <= 5:
            score += 2.0
        
        return min(score, 10.0)
    
    # === HOMEPAGE SECTIONS ===
    
    def create_homepage_section(
        self,
        section_type: str,
        title: str,
        video_ids: List[str],
        subtitle: str = "",
        display_order: int = 0,
        auto_update: bool = True
    ) -> HomepageSection:
        """Crée section homepage"""
        section = HomepageSection(
            section_type=section_type,
            title=title,
            subtitle=subtitle,
            video_ids=video_ids,
            display_order=display_order,
            auto_update=auto_update
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO homepage_sections (
                section_type, title, subtitle, video_ids, display_order,
                auto_update
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            section.section_type,
            section.title,
            section.subtitle,
            json.dumps(section.video_ids),
            section.display_order,
            1 if section.auto_update else 0
        ))
        
        section.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return section
    
    def update_trending_section(self, engagement_data: List[Dict[str, Any]]):
        """Met à jour section Trending basée sur engagement"""
        # Trie par engagement
        sorted_videos = sorted(
            engagement_data,
            key=lambda x: x.get("engagement_score", 0),
            reverse=True
        )
        
        # Top 6 vidéos
        top_video_ids = [v["video_id"] for v in sorted_videos[:6]]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update ou create
        cursor.execute("""
            INSERT OR REPLACE INTO homepage_sections (
                section_type, title, subtitle, video_ids, display_order,
                last_updated
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "trending",
            "🔥 Trending Now",
            "Les vidéos les plus populaires du moment",
            json.dumps(top_video_ids),
            1,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_homepage_sections(self) -> List[HomepageSection]:
        """Récupère sections homepage actives"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM homepage_sections
            WHERE is_active = 1
            ORDER BY display_order ASC
        """)
        
        sections = []
        for row in cursor.fetchall():
            section = HomepageSection(
                id=row[0],
                section_type=row[1],
                title=row[2],
                subtitle=row[3],
                video_ids=json.loads(row[4]) if row[4] else [],
                display_order=row[5],
                is_active=bool(row[6]),
                auto_update=bool(row[7]),
                update_frequency_hours=row[8]
            )
            sections.append(section)
        
        conn.close()
        return sections
    
    # === SEO METADATA ===
    
    def generate_seo_metadata(
        self,
        page_type: str,
        page_id: str,
        title: str,
        description: str,
        keywords: List[str],
        image_url: str = ""
    ) -> SEOMetadata:
        """Génère métadonnées SEO complètes"""
        metadata = SEOMetadata(
            title=title,
            description=description,
            keywords=keywords,
            og_title=title,
            og_description=description,
            og_image=image_url,
            canonical_url=f"https://only.com/{page_type}/{page_id}"
        )
        
        # Générer schema.org markup
        metadata.schema_markup = {
            "@context": "https://schema.org",
            "@type": "VideoObject" if page_type == "video" else "Article",
            "name": title,
            "description": description,
            "thumbnailUrl": image_url,
            "author": {
                "@type": "Person",
                "name": "Matt"
            }
        }
        
        # Sauvegarder
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO seo_metadata (
                page_type, page_id, title, description, keywords,
                og_title, og_description, og_image, canonical_url,
                schema_markup
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            page_type,
            page_id,
            metadata.title,
            metadata.description,
            json.dumps(metadata.keywords),
            metadata.og_title,
            metadata.og_description,
            metadata.og_image,
            metadata.canonical_url,
            json.dumps(metadata.schema_markup)
        ))
        
        conn.commit()
        conn.close()
        
        return metadata
    
    # === ANALYTICS ===
    
    def track_page_view(self, content_type: str, content_id: str, time_on_page: int = 0):
        """Track vue de page"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        cursor.execute("""
            INSERT INTO content_analytics (
                content_type, content_id, views, time_on_page_seconds, date
            ) VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(content_type, content_id, date) DO UPDATE SET
                views = views + 1,
                time_on_page_seconds = (time_on_page_seconds + ?) / 2
        """, (content_type, content_id, time_on_page, today, time_on_page))
        
        conn.commit()
        conn.close()
    
    def get_top_content(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère top contenu par vues"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                content_type,
                content_id,
                SUM(views) as total_views,
                AVG(time_on_page_seconds) as avg_time
            FROM content_analytics
            GROUP BY content_type, content_id
            ORDER BY total_views DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "content_type": row[0],
                "content_id": row[1],
                "total_views": row[2],
                "avg_time_seconds": round(row[3])
            })
        
        conn.close()
        return results


def main():
    """Test Blog Engine"""
    print("📝 Blog & Homepage Engine - Tests\n")
    
    engine = BlogEngine()
    
    # Test 1: Générer blog post
    print("1️⃣ Génération blog post...")
    post = engine.generate_blog_post(
        video_id="vid_001",
        video_title="Montage Vidéo Pro en 10 Minutes - Techniques Avancées",
        video_description="Dans ce tuto, je te montre comment faire un montage vidéo professionnel en 10 minutes. Techniques de cut, transitions, color grading rapide, et export optimisé.",
        category="tutorial",
        keywords=["montage", "editing", "premiere", "tutorial"]
    )
    print(f"   ✅ Post créé: {post.title}")
    print(f"   📊 SEO Score: {post.seo_score:.1f}/10")
    print(f"   🔗 Slug: {post.slug}")
    print(f"   ⏱️  Lecture: {post.read_time_minutes}min\n")
    
    # Test 2: Créer sections homepage
    print("2️⃣ Création sections homepage...")
    sections_data = [
        ("trending", "🔥 Trending Now", ["vid_001", "vid_002", "vid_003"]),
        ("latest", "🆕 Dernières Vidéos", ["vid_004", "vid_005", "vid_006"]),
        ("popular", "⭐ Most Popular", ["vid_007", "vid_008", "vid_009"])
    ]
    
    for section_type, title, video_ids in sections_data:
        section = engine.create_homepage_section(
            section_type=section_type,
            title=title,
            video_ids=video_ids,
            display_order=len(sections_data)
        )
        print(f"   ✅ Section: {section.title} ({len(section.video_ids)} vidéos)")
    print()
    
    # Test 3: Update trending section
    print("3️⃣ Update section Trending...")
    engagement_data = [
        {"video_id": "vid_010", "engagement_score": 9.5},
        {"video_id": "vid_011", "engagement_score": 9.2},
        {"video_id": "vid_012", "engagement_score": 8.8},
        {"video_id": "vid_013", "engagement_score": 8.5},
        {"video_id": "vid_014", "engagement_score": 8.2},
        {"video_id": "vid_015", "engagement_score": 7.9},
    ]
    engine.update_trending_section(engagement_data)
    print("   ✅ Section Trending mise à jour avec top 6\n")
    
    # Test 4: Générer SEO metadata
    print("4️⃣ Génération SEO metadata...")
    seo = engine.generate_seo_metadata(
        page_type="blog",
        page_id=post.slug,
        title=post.title,
        description=post.meta_description,
        keywords=post.keywords,
        image_url="https://cdn.only.com/thumbnails/vid_001.jpg"
    )
    print(f"   ✅ Meta title: {seo.title[:60]}...")
    print(f"   ✅ Schema.org: {seo.schema_markup['@type']}")
    print(f"   ✅ Canonical: {seo.canonical_url}\n")
    
    # Test 5: Track analytics
    print("5️⃣ Simulation analytics...")
    for i in range(150):
        engine.track_page_view("blog", post.slug, time_on_page=180)
    for i in range(89):
        engine.track_page_view("blog", post.slug, time_on_page=120)
    print("   ✅ 239 vues trackées\n")
    
    # Test 6: Top content
    print("6️⃣ Top contenu:")
    top = engine.get_top_content(limit=5)
    for i, item in enumerate(top, 1):
        print(f"   {i}. {item['content_id']}: {item['total_views']} vues, {item['avg_time_seconds']}s avg")
    
    print("\n✅ Blog Engine opérationnel!")


if __name__ == "__main__":
    main()
