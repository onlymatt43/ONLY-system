"""
Sales & Retention Engine - Phase 2 Module 1/3
Gère FOMO, scarcity, social proof, comeback campaigns
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timedelta
import sqlite3
import json
import random


class FOMOTechnique(Enum):
    """Techniques FOMO disponibles"""
    TIME_LIMITED = "time_limited"  # "Plus que 24h!"
    QUANTITY_LIMITED = "quantity_limited"  # "10 places restantes"
    EXCLUSIVE_ACCESS = "exclusive_access"  # "Accès VIP uniquement"
    FLASH_SALE = "flash_sale"  # "Promotion flash -50%"
    COUNTDOWN = "countdown"  # Timer visible
    SEASONAL = "seasonal"  # "Offre de Noël"
    EARLY_BIRD = "early_bird"  # "Early access"


class SocialProofType(Enum):
    """Types de social proof"""
    VIEWER_COUNT = "viewer_count"  # "1000+ viewers"
    TESTIMONIAL = "testimonial"  # "5 ⭐ sur 1200 avis"
    TRENDING = "trending"  # "#1 Trending"
    EXPERT_VALIDATION = "expert_validation"  # "Recommandé par..."
    USER_ACTIVITY = "user_activity"  # "45 personnes regardent maintenant"
    SUCCESS_STORIES = "success_stories"  # "+500 clients satisfaits"


class RetentionTrigger(Enum):
    """Déclencheurs de campagnes retention"""
    ABANDONED_CART = "abandoned_cart"  # Panier abandonné
    INACTIVE_USER = "inactive_user"  # Pas connecté depuis X jours
    TRIAL_ENDING = "trial_ending"  # Fin de période d'essai
    CONTENT_REMINDER = "content_reminder"  # Nouveau contenu
    PERSONALIZED_OFFER = "personalized_offer"  # Offre basée sur historique
    WIN_BACK = "win_back"  # Ancien client inactif


@dataclass
class FOMOCampaign:
    """Campagne FOMO"""
    id: Optional[int] = None
    technique: FOMOTechnique = FOMOTechnique.TIME_LIMITED
    message: str = ""
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    target_audience: str = "all"  # "all", "new", "returning", "vip"
    urgency_level: int = 5  # 1-10
    video_ids: List[str] = field(default_factory=list)
    is_active: bool = True
    conversion_rate: float = 0.0
    impressions: int = 0
    clicks: int = 0
    
    def is_expired(self) -> bool:
        """Vérifie si la campagne est expirée"""
        if not self.end_date:
            return False
        return datetime.now() > self.end_date
    
    def get_countdown_message(self) -> str:
        """Génère message avec countdown"""
        if not self.end_date:
            return self.message
        
        time_left = self.end_date - datetime.now()
        if time_left.total_seconds() <= 0:
            return "⚠️ TERMINÉ"
        
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        
        if hours > 24:
            days = hours // 24
            return f"⏰ Plus que {days}j {hours % 24}h - {self.message}"
        elif hours > 0:
            return f"⏰ Plus que {hours}h {minutes}min - {self.message}"
        else:
            return f"🔥 DERNIÈRE CHANCE! {minutes}min - {self.message}"


@dataclass
class SocialProof:
    """Preuve sociale"""
    id: Optional[int] = None
    proof_type: SocialProofType = SocialProofType.VIEWER_COUNT
    message: str = ""
    video_id: Optional[str] = None
    value: float = 0.0  # Count, rating, etc
    source: str = ""  # Où afficher
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def format_message(self) -> str:
        """Formate le message de social proof"""
        if self.proof_type == SocialProofType.VIEWER_COUNT:
            if self.value >= 1000:
                k_value = self.value / 1000
                return f"👥 {k_value:.1f}K+ viewers"
            return f"👥 {int(self.value)}+ viewers"
        
        elif self.proof_type == SocialProofType.TESTIMONIAL:
            return f"⭐ {self.value}/5 sur {self.message}"
        
        elif self.proof_type == SocialProofType.TRENDING:
            return f"🔥 #{int(self.value)} Trending"
        
        elif self.proof_type == SocialProofType.USER_ACTIVITY:
            return f"👀 {int(self.value)} personnes regardent maintenant"
        
        return self.message


@dataclass
class RetentionCampaign:
    """Campagne de rétention"""
    id: Optional[int] = None
    trigger: RetentionTrigger = RetentionTrigger.INACTIVE_USER
    name: str = ""
    delay_hours: int = 24  # Délai avant déclenchement
    message_template: str = ""
    offer: Optional[str] = None  # Offre spéciale
    discount_percentage: int = 0
    target_segment: str = "inactive"
    is_active: bool = True
    success_rate: float = 0.0
    sent_count: int = 0
    
    def format_message(self, user_data: Dict[str, Any]) -> str:
        """Génère message personnalisé"""
        message = self.message_template
        
        # Remplace variables
        if "{name}" in message and "name" in user_data:
            message = message.replace("{name}", user_data["name"])
        
        if "{offer}" in message and self.offer:
            message = message.replace("{offer}", self.offer)
        
        if "{discount}" in message and self.discount_percentage > 0:
            message = message.replace("{discount}", f"{self.discount_percentage}%")
        
        return message


class SalesEngine:
    """
    Moteur de ventes et rétention
    Gère FOMO, social proof, campagnes comeback
    """
    
    def __init__(self, db_path: str = "sales_engine.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table campagnes FOMO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fomo_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                technique TEXT NOT NULL,
                message TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                target_audience TEXT DEFAULT 'all',
                urgency_level INTEGER DEFAULT 5,
                video_ids TEXT,
                is_active INTEGER DEFAULT 1,
                conversion_rate REAL DEFAULT 0.0,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table social proof
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_proofs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proof_type TEXT NOT NULL,
                message TEXT NOT NULL,
                video_id TEXT,
                value REAL DEFAULT 0.0,
                source TEXT,
                is_verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table campagnes retention
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retention_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger TEXT NOT NULL,
                name TEXT NOT NULL,
                delay_hours INTEGER DEFAULT 24,
                message_template TEXT NOT NULL,
                offer TEXT,
                discount_percentage INTEGER DEFAULT 0,
                target_segment TEXT DEFAULT 'inactive',
                is_active INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 0.0,
                sent_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table triggers utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                triggered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                campaign_id INTEGER,
                is_processed INTEGER DEFAULT 0,
                processed_at TEXT,
                converted INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    # === FOMO CAMPAIGNS ===
    
    def create_fomo_campaign(
        self,
        technique: FOMOTechnique,
        message: str,
        duration_hours: Optional[int] = None,
        video_ids: Optional[List[str]] = None,
        target_audience: str = "all",
        urgency_level: int = 5
    ) -> FOMOCampaign:
        """Crée une campagne FOMO"""
        campaign = FOMOCampaign(
            technique=technique,
            message=message,
            target_audience=target_audience,
            urgency_level=urgency_level,
            video_ids=video_ids or []
        )
        
        if duration_hours:
            campaign.end_date = datetime.now() + timedelta(hours=duration_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO fomo_campaigns (
                technique, message, start_date, end_date, target_audience,
                urgency_level, video_ids
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign.technique.value,
            campaign.message,
            campaign.start_date.isoformat(),
            campaign.end_date.isoformat() if campaign.end_date else None,
            campaign.target_audience,
            campaign.urgency_level,
            json.dumps(campaign.video_ids)
        ))
        
        campaign.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return campaign
    
    def get_active_fomo_campaigns(self, audience: str = "all") -> List[FOMOCampaign]:
        """Récupère campagnes FOMO actives"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM fomo_campaigns
            WHERE is_active = 1
            AND (target_audience = ? OR target_audience = 'all')
            AND (end_date IS NULL OR end_date > ?)
            ORDER BY urgency_level DESC
        """, (audience, datetime.now().isoformat()))
        
        campaigns = []
        for row in cursor.fetchall():
            campaign = FOMOCampaign(
                id=row[0],
                technique=FOMOTechnique(row[1]),
                message=row[2],
                start_date=datetime.fromisoformat(row[3]),
                end_date=datetime.fromisoformat(row[4]) if row[4] else None,
                target_audience=row[5],
                urgency_level=row[6],
                video_ids=json.loads(row[7]) if row[7] else [],
                is_active=bool(row[8]),
                conversion_rate=row[9],
                impressions=row[10],
                clicks=row[11]
            )
            campaigns.append(campaign)
        
        conn.close()
        return campaigns
    
    def track_fomo_interaction(self, campaign_id: int, action: str = "impression"):
        """Track interaction avec campagne FOMO"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if action == "impression":
            cursor.execute("""
                UPDATE fomo_campaigns
                SET impressions = impressions + 1
                WHERE id = ?
            """, (campaign_id,))
        elif action == "click":
            cursor.execute("""
                UPDATE fomo_campaigns
                SET clicks = clicks + 1
                WHERE id = ?
            """, (campaign_id,))
            
            # Calcul conversion rate
            cursor.execute("""
                UPDATE fomo_campaigns
                SET conversion_rate = CAST(clicks AS REAL) / impressions
                WHERE id = ? AND impressions > 0
            """, (campaign_id,))
        
        conn.commit()
        conn.close()
    
    # === SOCIAL PROOF ===
    
    def add_social_proof(
        self,
        proof_type: SocialProofType,
        message: str,
        value: float,
        video_id: Optional[str] = None,
        source: str = "homepage",
        is_verified: bool = False
    ) -> SocialProof:
        """Ajoute une preuve sociale"""
        proof = SocialProof(
            proof_type=proof_type,
            message=message,
            value=value,
            video_id=video_id,
            source=source,
            is_verified=is_verified
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO social_proofs (
                proof_type, message, video_id, value, source, is_verified
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            proof.proof_type.value,
            proof.message,
            proof.video_id,
            proof.value,
            proof.source,
            1 if proof.is_verified else 0
        ))
        
        proof.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return proof
    
    def get_social_proofs(self, video_id: Optional[str] = None) -> List[SocialProof]:
        """Récupère preuves sociales"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if video_id:
            cursor.execute("""
                SELECT * FROM social_proofs
                WHERE video_id = ? OR video_id IS NULL
                ORDER BY is_verified DESC, created_at DESC
            """, (video_id,))
        else:
            cursor.execute("""
                SELECT * FROM social_proofs
                WHERE video_id IS NULL
                ORDER BY is_verified DESC, created_at DESC
            """)
        
        proofs = []
        for row in cursor.fetchall():
            proof = SocialProof(
                id=row[0],
                proof_type=SocialProofType(row[1]),
                message=row[2],
                video_id=row[3],
                value=row[4],
                source=row[5],
                is_verified=bool(row[6]),
                created_at=datetime.fromisoformat(row[7])
            )
            proofs.append(proof)
        
        conn.close()
        return proofs
    
    # === RETENTION CAMPAIGNS ===
    
    def create_retention_campaign(
        self,
        trigger: RetentionTrigger,
        name: str,
        message_template: str,
        delay_hours: int = 24,
        offer: Optional[str] = None,
        discount_percentage: int = 0,
        target_segment: str = "inactive"
    ) -> RetentionCampaign:
        """Crée campagne de rétention"""
        campaign = RetentionCampaign(
            trigger=trigger,
            name=name,
            message_template=message_template,
            delay_hours=delay_hours,
            offer=offer,
            discount_percentage=discount_percentage,
            target_segment=target_segment
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO retention_campaigns (
                trigger, name, delay_hours, message_template, offer,
                discount_percentage, target_segment
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign.trigger.value,
            campaign.name,
            campaign.delay_hours,
            campaign.message_template,
            campaign.offer,
            campaign.discount_percentage,
            campaign.target_segment
        ))
        
        campaign.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return campaign
    
    def trigger_retention_event(
        self,
        user_id: str,
        trigger_type: RetentionTrigger
    ):
        """Enregistre événement déclencheur de rétention"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cherche campagne active pour ce trigger
        cursor.execute("""
            SELECT id FROM retention_campaigns
            WHERE trigger = ? AND is_active = 1
            LIMIT 1
        """, (trigger_type.value,))
        
        result = cursor.fetchone()
        campaign_id = result[0] if result else None
        
        # Enregistre trigger
        cursor.execute("""
            INSERT INTO user_triggers (user_id, trigger_type, campaign_id)
            VALUES (?, ?, ?)
        """, (user_id, trigger_type.value, campaign_id))
        
        conn.commit()
        conn.close()
    
    def get_pending_retention_actions(self) -> List[Dict[str, Any]]:
        """Récupère actions de rétention à envoyer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ut.id,
                ut.user_id,
                ut.trigger_type,
                ut.triggered_at,
                rc.id,
                rc.name,
                rc.message_template,
                rc.offer,
                rc.discount_percentage,
                rc.delay_hours
            FROM user_triggers ut
            JOIN retention_campaigns rc ON ut.campaign_id = rc.id
            WHERE ut.is_processed = 0
            AND rc.is_active = 1
            AND datetime(ut.triggered_at, '+' || rc.delay_hours || ' hours') <= datetime('now')
        """)
        
        actions = []
        for row in cursor.fetchall():
            actions.append({
                "trigger_id": row[0],
                "user_id": row[1],
                "trigger_type": row[2],
                "triggered_at": row[3],
                "campaign_id": row[4],
                "campaign_name": row[5],
                "message_template": row[6],
                "offer": row[7],
                "discount": row[8],
                "delay_hours": row[9]
            })
        
        conn.close()
        return actions
    
    def mark_retention_action_sent(self, trigger_id: int, converted: bool = False):
        """Marque action retention comme envoyée"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_triggers
            SET is_processed = 1,
                processed_at = ?,
                converted = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), 1 if converted else 0, trigger_id))
        
        # Update stats campagne
        cursor.execute("""
            UPDATE retention_campaigns
            SET sent_count = sent_count + 1
            WHERE id = (SELECT campaign_id FROM user_triggers WHERE id = ?)
        """, (trigger_id,))
        
        conn.commit()
        conn.close()
    
    # === ANALYTICS ===
    
    def get_campaign_stats(self) -> Dict[str, Any]:
        """Récupère statistiques globales"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Stats FOMO
        cursor.execute("""
            SELECT 
                COUNT(*) as total_campaigns,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                AVG(conversion_rate) as avg_conversion
            FROM fomo_campaigns
            WHERE is_active = 1
        """)
        fomo_stats = cursor.fetchone()
        
        # Stats retention
        cursor.execute("""
            SELECT 
                COUNT(*) as total_campaigns,
                SUM(sent_count) as total_sent,
                AVG(success_rate) as avg_success
            FROM retention_campaigns
            WHERE is_active = 1
        """)
        retention_stats = cursor.fetchone()
        
        # Stats social proof
        cursor.execute("""
            SELECT 
                COUNT(*) as total_proofs,
                AVG(value) as avg_value
            FROM social_proofs
        """)
        proof_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "fomo": {
                "total_campaigns": fomo_stats[0] or 0,
                "total_impressions": fomo_stats[1] or 0,
                "total_clicks": fomo_stats[2] or 0,
                "avg_conversion_rate": round(fomo_stats[3] or 0, 3)
            },
            "retention": {
                "total_campaigns": retention_stats[0] or 0,
                "total_sent": retention_stats[1] or 0,
                "avg_success_rate": round(retention_stats[2] or 0, 3)
            },
            "social_proof": {
                "total_proofs": proof_stats[0] or 0,
                "avg_value": round(proof_stats[1] or 0, 1)
            }
        }


def main():
    """Test du Sales Engine"""
    print("🎯 Sales & Retention Engine - Tests\n")
    
    engine = SalesEngine()
    
    # Test 1: Campagne FOMO flash sale
    print("1️⃣ Création campagne FOMO Flash Sale...")
    fomo = engine.create_fomo_campaign(
        technique=FOMOTechnique.FLASH_SALE,
        message="🔥 FLASH SALE -50% sur toutes les vidéos premium!",
        duration_hours=24,
        urgency_level=10,
        target_audience="all"
    )
    print(f"   ✅ Campagne créée (ID: {fomo.id})")
    print(f"   Message: {fomo.get_countdown_message()}\n")
    
    # Test 2: Social proof
    print("2️⃣ Ajout Social Proofs...")
    proofs = [
        engine.add_social_proof(
            proof_type=SocialProofType.VIEWER_COUNT,
            message="",
            value=15000,
            source="homepage",
            is_verified=True
        ),
        engine.add_social_proof(
            proof_type=SocialProofType.TESTIMONIAL,
            message="2543 avis",
            value=4.8,
            source="homepage",
            is_verified=True
        ),
        engine.add_social_proof(
            proof_type=SocialProofType.USER_ACTIVITY,
            message="",
            value=127,
            source="video_page",
            is_verified=False
        )
    ]
    for proof in proofs:
        print(f"   ✅ {proof.format_message()}")
    print()
    
    # Test 3: Campagne retention
    print("3️⃣ Création campagne Retention (Win-Back)...")
    retention = engine.create_retention_campaign(
        trigger=RetentionTrigger.WIN_BACK,
        name="Comeback Special",
        message_template="Hey {name}! 👋\n\nÇa fait longtemps! On a du nouveau contenu INSANE pour toi.\n\n{offer} spéciale: -{discount} sur ton retour! 🔥",
        delay_hours=72,
        offer="Offre exclusive",
        discount_percentage=30,
        target_segment="inactive_30days"
    )
    print(f"   ✅ Campagne créée: {retention.name}")
    print(f"   Délai: {retention.delay_hours}h, Discount: {retention.discount_percentage}%\n")
    
    # Test 4: Trigger retention event
    print("4️⃣ Simulation trigger retention...")
    engine.trigger_retention_event(
        user_id="user_12345",
        trigger_type=RetentionTrigger.WIN_BACK
    )
    print("   ✅ Event enregistré pour user_12345\n")
    
    # Test 5: Track FOMO interactions
    print("5️⃣ Simulation interactions FOMO...")
    if fomo.id:
        for i in range(150):
            engine.track_fomo_interaction(fomo.id, "impression")
        for i in range(23):
            engine.track_fomo_interaction(fomo.id, "click")
    print("   ✅ 150 impressions, 23 clicks trackés\n")
    
    # Test 6: Stats globales
    print("6️⃣ Statistiques globales:")
    stats = engine.get_campaign_stats()
    print(f"""
   📊 FOMO:
      • {stats['fomo']['total_campaigns']} campagnes actives
      • {stats['fomo']['total_impressions']} impressions
      • {stats['fomo']['total_clicks']} clicks
      • {stats['fomo']['avg_conversion_rate']*100:.1f}% conversion
   
   📊 Retention:
      • {stats['retention']['total_campaigns']} campagnes actives
      • {stats['retention']['total_sent']} messages envoyés
   
   📊 Social Proof:
      • {stats['social_proof']['total_proofs']} preuves actives
      • Valeur moyenne: {stats['social_proof']['avg_value']}
    """)
    
    print("\n✅ Sales Engine opérationnel!")


if __name__ == "__main__":
    main()
