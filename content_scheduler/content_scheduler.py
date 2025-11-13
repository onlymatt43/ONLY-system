"""
Content Scheduler - Automatisation complète des posts
Schedule, pause, resume posts pour créer retention & FOMO
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


# ==================== ENUMS ====================

class Platform(str, Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    BLUESKY = "bluesky"


class ScheduleStatus(str, Enum):
    SCHEDULED = "scheduled"      # Programmé, en attente
    PAUSED = "paused"            # Mis en pause
    PUBLISHED = "published"      # Publié avec succès
    FAILED = "failed"            # Échec publication
    CANCELLED = "cancelled"      # Annulé


class RetentionStrategy(str, Enum):
    REGULAR = "regular"              # Posting régulier
    BURST = "burst"                  # Burst 3-5 posts rapides puis pause
    CLIFFHANGER = "cliffhanger"      # Série avec cliffhangers
    COMEBACK = "comeback"            # Long silence puis comeback
    TEASER_RELEASE = "teaser_release"  # Teaser avant release


# ==================== DATA MODELS ====================

@dataclass
class ScheduledPost:
    """Post programmé avec metadata"""
    
    id: Optional[int] = None
    video_id: str = ""
    platform: str = Platform.TWITTER.value
    
    # Content
    generated_content: str = ""
    style_match_score: float = 0.0
    
    # Scheduling
    scheduled_time: str = ""  # ISO format
    status: str = ScheduleStatus.SCHEDULED.value
    
    # Retention strategy
    strategy: str = RetentionStrategy.REGULAR.value
    series_id: Optional[str] = None  # Pour grouper posts (séries, comebacks)
    is_teaser: bool = False
    
    # Analytics
    published_at: Optional[str] = None
    engagement_predicted: float = 0.0
    engagement_actual: Optional[float] = None
    
    # Metadata
    created_at: str = ""
    updated_at: str = ""


@dataclass
class ScheduleCalendar:
    """Calendrier de scheduling avec slots optimaux"""
    
    platform: str
    
    # Optimal posting times (24h format)
    optimal_hours: List[int]  # [9, 12, 18, 21]
    
    # Posts per week target
    posts_per_week: int
    
    # Current schedule
    scheduled_count: int
    next_available_slot: Optional[str]  # ISO datetime


@dataclass
class RetentionMetrics:
    """Métriques retention & engagement"""
    
    total_scheduled: int
    total_published: int
    total_paused: int
    
    avg_engagement_predicted: float
    avg_engagement_actual: float
    
    best_performing_platform: str
    best_performing_time: str
    
    series_completion_rate: float  # % séries complétées
    comeback_impact: float  # Boost engagement après comeback


# ==================== CONTENT SCHEDULER ====================

class ContentScheduler:
    """Gestionnaire de scheduling avec stratégies retention"""
    
    def __init__(self, db_path: str = "./scheduler.db"):
        self.db_path = db_path
        self._init_database()
        
        # Platform optimal times (based on industry research)
        self.platform_optimal_hours = {
            Platform.TWITTER: [9, 12, 15, 18, 21],      # Peaks: matin, lunch, soir
            Platform.INSTAGRAM: [11, 13, 19, 21],       # Lunch & evening
            Platform.FACEBOOK: [9, 13, 15, 18],         # Morning & afternoon
            Platform.LINKEDIN: [8, 12, 17],             # Business hours
            Platform.BLUESKY: [10, 14, 20]              # Mid-day & evening
        }
        
        # Default posts per week per platform
        self.default_posts_per_week = {
            Platform.TWITTER: 7,      # Daily
            Platform.INSTAGRAM: 5,     # 5x/week
            Platform.FACEBOOK: 4,      # 4x/week
            Platform.LINKEDIN: 3,      # 3x/week
            Platform.BLUESKY: 5        # 5x/week
        }
    
    def _init_database(self):
        """Initialize SQLite database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Scheduled posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                generated_content TEXT NOT NULL,
                style_match_score REAL DEFAULT 0.0,
                scheduled_time TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                strategy TEXT DEFAULT 'regular',
                series_id TEXT,
                is_teaser INTEGER DEFAULT 0,
                published_at TEXT,
                engagement_predicted REAL DEFAULT 0.0,
                engagement_actual REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Series tracking (pour cliffhangers, comebacks)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS series (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                strategy TEXT NOT NULL,
                video_ids TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL
            )
        """)
        
        # Analytics tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES scheduled_posts(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def schedule_post(
        self,
        video_id: str,
        platform: Platform,
        generated_content: str,
        style_match_score: float,
        scheduled_time: Optional[datetime] = None,
        strategy: RetentionStrategy = RetentionStrategy.REGULAR,
        series_id: Optional[str] = None,
        is_teaser: bool = False
    ) -> ScheduledPost:
        """
        Schedule un post pour publication
        
        Args:
            video_id: ID vidéo
            platform: Platform cible
            generated_content: Post généré par Style Learner
            style_match_score: Score match style (0-1)
            scheduled_time: Datetime publication (auto si None)
            strategy: Stratégie retention
            series_id: ID série si fait partie d'une série
            is_teaser: Est-ce un teaser?
            
        Returns:
            ScheduledPost créé
        """
        
        # Auto-schedule si pas de time fourni
        if not scheduled_time:
            scheduled_time = self._get_next_optimal_slot(platform)
        
        now = datetime.utcnow().isoformat()
        
        post = ScheduledPost(
            video_id=video_id,
            platform=platform.value,
            generated_content=generated_content,
            style_match_score=style_match_score,
            scheduled_time=scheduled_time.isoformat(),
            status=ScheduleStatus.SCHEDULED.value,
            strategy=strategy.value,
            series_id=series_id,
            is_teaser=is_teaser,
            engagement_predicted=self._predict_engagement(
                platform, scheduled_time, style_match_score
            ),
            created_at=now,
            updated_at=now
        )
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO scheduled_posts (
                video_id, platform, generated_content, style_match_score,
                scheduled_time, status, strategy, series_id, is_teaser,
                engagement_predicted, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post.video_id, post.platform, post.generated_content,
            post.style_match_score, post.scheduled_time, post.status,
            post.strategy, post.series_id, int(post.is_teaser),
            post.engagement_predicted, post.created_at, post.updated_at
        ))
        
        post.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return post
    
    def _get_next_optimal_slot(self, platform: Platform) -> datetime:
        """Trouve prochain slot optimal pour platform"""
        
        optimal_hours = self.platform_optimal_hours.get(platform, [12, 18])
        
        now = datetime.utcnow()
        current_hour = now.hour
        
        # Trouve prochaine heure optimale
        next_hour = None
        for hour in optimal_hours:
            if hour > current_hour:
                next_hour = hour
                break
        
        # Si aucune heure aujourd'hui, prends première heure demain
        if next_hour is None:
            next_day = now + timedelta(days=1)
            return next_day.replace(hour=optimal_hours[0], minute=0, second=0)
        
        return now.replace(hour=next_hour, minute=0, second=0)
    
    def _predict_engagement(
        self,
        platform: Platform,
        scheduled_time: datetime,
        style_match_score: float
    ) -> float:
        """
        Prédit engagement basé sur platform, time, style
        
        Returns:
            Score 0-10
        """
        
        base_score = 5.0
        
        # Bonus si optimal hour
        optimal_hours = self.platform_optimal_hours.get(platform, [])
        if scheduled_time.hour in optimal_hours:
            base_score += 1.5
        
        # Bonus si style match élevé
        if style_match_score >= 0.8:
            base_score += 2.0
        elif style_match_score >= 0.6:
            base_score += 1.0
        
        # Platform multipliers (based on typical engagement)
        platform_multipliers = {
            Platform.TWITTER: 1.0,
            Platform.INSTAGRAM: 1.2,
            Platform.FACEBOOK: 0.8,
            Platform.LINKEDIN: 0.9,
            Platform.BLUESKY: 1.1
        }
        
        multiplier = platform_multipliers.get(platform, 1.0)
        final_score = base_score * multiplier
        
        return min(10.0, final_score)
    
    def schedule_series(
        self,
        video_ids: List[str],
        platform: Platform,
        strategy: RetentionStrategy,
        series_name: str,
        start_date: datetime
    ) -> List[ScheduledPost]:
        """
        Schedule une série de posts avec stratégie
        
        Args:
            video_ids: Liste IDs vidéos
            platform: Platform
            strategy: CLIFFHANGER ou BURST ou TEASER_RELEASE
            series_name: Nom série
            start_date: Date début
            
        Returns:
            Liste ScheduledPosts créés
        """
        
        series_id = f"series_{datetime.utcnow().timestamp()}"
        
        # Save series to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO series (
                id, name, strategy, video_ids, start_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            series_id, series_name, strategy.value,
            json.dumps(video_ids), start_date.isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Schedule posts selon stratégie
        posts = []
        
        if strategy == RetentionStrategy.CLIFFHANGER:
            # Espace 2-3 jours entre posts, crée tension
            posts = self._schedule_cliffhanger_series(
                video_ids, platform, series_id, start_date
            )
        
        elif strategy == RetentionStrategy.BURST:
            # 3-5 posts rapides (1-2h spacing) puis long silence
            posts = self._schedule_burst_series(
                video_ids, platform, series_id, start_date
            )
        
        elif strategy == RetentionStrategy.TEASER_RELEASE:
            # Teasers 3-5 jours avant, puis release
            posts = self._schedule_teaser_release(
                video_ids, platform, series_id, start_date
            )
        
        return posts
    
    def _schedule_cliffhanger_series(
        self,
        video_ids: List[str],
        platform: Platform,
        series_id: str,
        start_date: datetime
    ) -> List[ScheduledPost]:
        """Schedule série avec cliffhangers (2-3 jours spacing)"""
        
        posts = []
        current_time = start_date
        
        for i, video_id in enumerate(video_ids):
            # Génère content (integration avec Style Learner needed)
            content = f"[CLIFFHANGER {i+1}/{len(video_ids)}] - Generated content here"
            
            post = self.schedule_post(
                video_id=video_id,
                platform=platform,
                generated_content=content,
                style_match_score=0.8,  # Placeholder
                scheduled_time=current_time,
                strategy=RetentionStrategy.CLIFFHANGER,
                series_id=series_id,
                is_teaser=False
            )
            
            posts.append(post)
            
            # Next post 2-3 jours plus tard
            current_time += timedelta(days=2.5)
        
        return posts
    
    def _schedule_burst_series(
        self,
        video_ids: List[str],
        platform: Platform,
        series_id: str,
        start_date: datetime
    ) -> List[ScheduledPost]:
        """Schedule burst: 3-5 posts rapides (1-2h spacing)"""
        
        posts = []
        current_time = start_date
        
        for i, video_id in enumerate(video_ids):
            content = f"[BURST {i+1}/{len(video_ids)}] - Generated content here"
            
            post = self.schedule_post(
                video_id=video_id,
                platform=platform,
                generated_content=content,
                style_match_score=0.8,
                scheduled_time=current_time,
                strategy=RetentionStrategy.BURST,
                series_id=series_id
            )
            
            posts.append(post)
            
            # Next post 1-2h plus tard
            current_time += timedelta(hours=1.5)
        
        return posts
    
    def _schedule_teaser_release(
        self,
        video_ids: List[str],
        platform: Platform,
        series_id: str,
        start_date: datetime
    ) -> List[ScheduledPost]:
        """Schedule teasers avant release principal"""
        
        posts = []
        
        # Main release (dernier video_id)
        main_video_id = video_ids[-1]
        teaser_video_ids = video_ids[:-1]
        
        # Release time
        release_time = start_date
        
        # Schedule teasers 3-5 jours avant
        current_time = release_time - timedelta(days=len(teaser_video_ids) * 2)
        
        for i, video_id in enumerate(teaser_video_ids):
            content = f"[TEASER {i+1}] - Coming soon... 👀"
            
            post = self.schedule_post(
                video_id=video_id,
                platform=platform,
                generated_content=content,
                style_match_score=0.8,
                scheduled_time=current_time,
                strategy=RetentionStrategy.TEASER_RELEASE,
                series_id=series_id,
                is_teaser=True
            )
            
            posts.append(post)
            current_time += timedelta(days=2)
        
        # Schedule main release
        main_post = self.schedule_post(
            video_id=main_video_id,
            platform=platform,
            generated_content="[RELEASE] - It's finally here! 🔥",
            style_match_score=0.9,
            scheduled_time=release_time,
            strategy=RetentionStrategy.TEASER_RELEASE,
            series_id=series_id,
            is_teaser=False
        )
        
        posts.append(main_post)
        
        return posts
    
    def pause_post(self, post_id: int) -> bool:
        """Pause un post programmé"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scheduled_posts
            SET status = ?, updated_at = ?
            WHERE id = ? AND status = 'scheduled'
        """, (ScheduleStatus.PAUSED.value, datetime.utcnow().isoformat(), post_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def resume_post(self, post_id: int) -> bool:
        """Resume un post pausé"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scheduled_posts
            SET status = ?, updated_at = ?
            WHERE id = ? AND status = 'paused'
        """, (ScheduleStatus.SCHEDULED.value, datetime.utcnow().isoformat(), post_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def cancel_post(self, post_id: int) -> bool:
        """Annule un post"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scheduled_posts
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (ScheduleStatus.CANCELLED.value, datetime.utcnow().isoformat(), post_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_scheduled_posts(
        self,
        platform: Optional[Platform] = None,
        status: Optional[ScheduleStatus] = None,
        limit: int = 50
    ) -> List[ScheduledPost]:
        """Récupère posts programmés avec filtres"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM scheduled_posts WHERE 1=1"
        params = []
        
        if platform:
            query += " AND platform = ?"
            params.append(platform.value)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY scheduled_time ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        posts = []
        for row in rows:
            post = ScheduledPost(
                id=row[0],
                video_id=row[1],
                platform=row[2],
                generated_content=row[3],
                style_match_score=row[4],
                scheduled_time=row[5],
                status=row[6],
                strategy=row[7],
                series_id=row[8],
                is_teaser=bool(row[9]),
                published_at=row[10],
                engagement_predicted=row[11],
                engagement_actual=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
            posts.append(post)
        
        return posts
    
    def get_calendar(self, platform: Platform) -> ScheduleCalendar:
        """Récupère calendrier pour platform"""
        
        optimal_hours = self.platform_optimal_hours.get(platform, [12, 18])
        posts_per_week = self.default_posts_per_week.get(platform, 5)
        
        # Count scheduled posts
        scheduled_posts = self.get_scheduled_posts(
            platform=platform,
            status=ScheduleStatus.SCHEDULED
        )
        
        next_slot = self._get_next_optimal_slot(platform)
        
        return ScheduleCalendar(
            platform=platform.value,
            optimal_hours=optimal_hours,
            posts_per_week=posts_per_week,
            scheduled_count=len(scheduled_posts),
            next_available_slot=next_slot.isoformat()
        )
    
    def get_retention_metrics(self) -> RetentionMetrics:
        """Calcule métriques retention globales"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM scheduled_posts WHERE status = 'scheduled'")
        total_scheduled = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scheduled_posts WHERE status = 'published'")
        total_published = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scheduled_posts WHERE status = 'paused'")
        total_paused = cursor.fetchone()[0]
        
        # Averages
        cursor.execute("SELECT AVG(engagement_predicted) FROM scheduled_posts")
        avg_predicted = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT AVG(engagement_actual) FROM scheduled_posts WHERE engagement_actual IS NOT NULL")
        avg_actual = cursor.fetchone()[0] or 0.0
        
        # Best performing platform
        cursor.execute("""
            SELECT platform, AVG(engagement_actual) as avg_eng
            FROM scheduled_posts
            WHERE engagement_actual IS NOT NULL
            GROUP BY platform
            ORDER BY avg_eng DESC
            LIMIT 1
        """)
        best_platform_row = cursor.fetchone()
        best_platform = best_platform_row[0] if best_platform_row else "twitter"
        
        # Best performing time (hour)
        cursor.execute("""
            SELECT strftime('%H', scheduled_time) as hour, AVG(engagement_actual) as avg_eng
            FROM scheduled_posts
            WHERE engagement_actual IS NOT NULL
            GROUP BY hour
            ORDER BY avg_eng DESC
            LIMIT 1
        """)
        best_time_row = cursor.fetchone()
        best_time = f"{best_time_row[0]}:00" if best_time_row else "12:00"
        
        # Series completion rate
        cursor.execute("SELECT COUNT(*) FROM series WHERE status = 'completed'")
        completed_series = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM series")
        total_series = cursor.fetchone()[0]
        
        completion_rate = (completed_series / total_series * 100) if total_series > 0 else 0.0
        
        conn.close()
        
        return RetentionMetrics(
            total_scheduled=total_scheduled,
            total_published=total_published,
            total_paused=total_paused,
            avg_engagement_predicted=round(avg_predicted, 2),
            avg_engagement_actual=round(avg_actual, 2),
            best_performing_platform=best_platform,
            best_performing_time=best_time,
            series_completion_rate=round(completion_rate, 1),
            comeback_impact=1.5  # Placeholder - track actual
        )


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """Test du Content Scheduler"""
    
    print("📅 Content Scheduler - Test")
    print("=" * 60)
    
    # Initialize
    scheduler = ContentScheduler(db_path="./test_scheduler.db")
    
    # 1. Schedule single post
    print("\n1️⃣ Scheduling single post...")
    
    post = scheduler.schedule_post(
        video_id="123",
        platform=Platform.TWITTER,
        generated_content="🔥 OK LES GARS - Check cette vidéo insane! 💯",
        style_match_score=0.85,
        strategy=RetentionStrategy.REGULAR
    )
    
    print(f"✅ Post scheduled!")
    print(f"  ID: {post.id}")
    print(f"  Platform: {post.platform}")
    print(f"  Scheduled: {post.scheduled_time}")
    print(f"  Predicted engagement: {post.engagement_predicted:.1f}/10")
    
    # 2. Schedule cliffhanger series
    print("\n\n2️⃣ Scheduling cliffhanger series...")
    
    series_posts = scheduler.schedule_series(
        video_ids=["456", "457", "458"],
        platform=Platform.INSTAGRAM,
        strategy=RetentionStrategy.CLIFFHANGER,
        series_name="Epic Tutorial Series",
        start_date=datetime.utcnow() + timedelta(days=1)
    )
    
    print(f"✅ Series scheduled: {len(series_posts)} posts")
    for i, p in enumerate(series_posts):
        print(f"  Post {i+1}: {p.scheduled_time} - {p.strategy}")
    
    # 3. Get calendar
    print("\n\n3️⃣ Getting calendar for Twitter...")
    
    calendar = scheduler.get_calendar(Platform.TWITTER)
    print(f"✅ Calendar:")
    print(f"  Optimal hours: {calendar.optimal_hours}")
    print(f"  Posts/week target: {calendar.posts_per_week}")
    print(f"  Currently scheduled: {calendar.scheduled_count}")
    print(f"  Next slot: {calendar.next_available_slot}")
    
    # 4. Get retention metrics
    print("\n\n4️⃣ Retention metrics...")
    
    metrics = scheduler.get_retention_metrics()
    print(f"✅ Metrics:")
    print(f"  Total scheduled: {metrics.total_scheduled}")
    print(f"  Total published: {metrics.total_published}")
    print(f"  Avg predicted engagement: {metrics.avg_engagement_predicted:.1f}/10")
    print(f"  Best platform: {metrics.best_performing_platform}")
    print(f"  Best time: {metrics.best_performing_time}")
    
    print("\n" + "=" * 60)
    print("✅ Content Scheduler tests completed!")
