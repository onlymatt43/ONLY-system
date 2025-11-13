"""
Consumer Chat System - Phase 2 Module 2/3
AI-powered chat pour guider achat, recommandations, objections
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import sqlite3
import json
import re


class UserIntent(Enum):
    """Intents utilisateur détectés"""
    BROWSING = "browsing"  # Juste regarde
    INTERESTED = "interested"  # Intéressé mais hésite
    READY_TO_BUY = "ready_to_buy"  # Prêt à acheter
    PRICE_CONCERN = "price_concern"  # Inquiet du prix
    TECHNICAL_QUESTION = "technical_question"  # Question technique
    OBJECTION = "objection"  # Objection (trop cher, pas sûr, etc)
    SUPPORT_REQUEST = "support_request"  # Demande support
    COMPARISON = "comparison"  # Compare avec alternatives


class ConversationStage(Enum):
    """Étapes de la conversation"""
    GREETING = "greeting"
    DISCOVERY = "discovery"  # Découvrir besoins
    RECOMMENDATION = "recommendation"  # Recommander contenu
    OBJECTION_HANDLING = "objection_handling"  # Traiter objections
    CLOSING = "closing"  # Closer la vente
    POST_PURCHASE = "post_purchase"  # Après achat


@dataclass
class ChatMessage:
    """Message dans conversation"""
    id: Optional[int] = None
    session_id: str = ""
    role: str = "user"  # user, assistant, system
    content: str = ""
    intent: Optional[UserIntent] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """Profil utilisateur pour personnalisation"""
    user_id: str = ""
    viewed_videos: List[str] = field(default_factory=list)
    favorite_topics: List[str] = field(default_factory=list)
    budget_range: Optional[str] = None  # "low", "medium", "high"
    purchase_history: List[str] = field(default_factory=list)
    objections_raised: List[str] = field(default_factory=list)
    engagement_score: float = 0.0  # 0-10
    last_active: datetime = field(default_factory=datetime.now)


@dataclass
class Recommendation:
    """Recommandation de vidéo"""
    video_id: str
    title: str
    reason: str  # Pourquoi recommandé
    relevance_score: float  # 0-1
    price: Optional[float] = None
    preview_available: bool = True


class ConsumerChatAI:
    """
    AI Chat pour consumer
    Intent detection, recommendations, objection handling
    """
    
    def __init__(self, db_path: str = "consumer_chat.db"):
        self.db_path = db_path
        self._init_database()
        
        # Pattern recognition pour intent detection
        self.intent_patterns = {
            UserIntent.PRICE_CONCERN: [
                r"trop cher", r"combien", r"prix", r"coût", r"€", r"\$",
                r"budget", r"abordable", r"gratuit", r"discount"
            ],
            UserIntent.READY_TO_BUY: [
                r"acheter", r"commander", r"payer", r"prendre", r"go",
                r"ok", r"d'accord", r"lets go", r"comment (je )?(fais|procède)"
            ],
            UserIntent.OBJECTION: [
                r"pas sûr", r"hésite", r"mais", r"problème", r"inquiet",
                r"risque", r"garantie", r"remboursement"
            ],
            UserIntent.COMPARISON: [
                r"comparer", r"différence", r"meilleur", r"alternative",
                r"ou bien", r"versus", r"vs", r"plutôt"
            ],
            UserIntent.TECHNICAL_QUESTION: [
                r"comment", r"pourquoi", r"qu'est-ce que", r"c'est quoi",
                r"format", r"durée", r"résolution", r"qualité"
            ]
        }
        
        # Réponses aux objections communes
        self.objection_responses = {
            "trop_cher": {
                "response": "Je comprends! 💰\n\nRegarde ça comme un investissement dans tes skills. Une seule vidéo peut te faire économiser 10h de recherche.\n\nEt on a une garantie satisfait ou remboursé 30j. Zéro risque! 🔒",
                "offer": "discount_10"
            },
            "pas_sur_qualite": {
                "response": "T'as raison de vérifier! 👌\n\nRegarde la preview COMPLÈTE ici → toutes mes vidéos ont des extraits gratuits.\n\nEt on a +1500 clients avec 4.8/5 ⭐ de moyenne!",
                "offer": "free_preview"
            },
            "pas_le_temps": {
                "response": "Justement! ⚡\n\nMes vidéos sont conçues pour aller DROIT AU BUT. Pas de blabla.\n\nTu peux regarder par séquences de 5min, et revenir quand tu veux. Accès illimité! 🎯",
                "offer": None
            },
            "debutant": {
                "response": "PARFAIT pour toi alors! 🎓\n\nJ'explique TOUT depuis zéro. Même ma grand-mère comprend lol.\n\nEt tu peux me poser des questions direct dans les commentaires! 💬",
                "offer": "beginner_bundle"
            }
        }
    
    def _init_database(self):
        """Initialise base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                user_id TEXT,
                stage TEXT DEFAULT 'greeting',
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_message_at TEXT,
                converted INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0
            )
        """)
        
        # Table messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                confidence REAL DEFAULT 0.0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Table user profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                viewed_videos TEXT,
                favorite_topics TEXT,
                budget_range TEXT,
                purchase_history TEXT,
                objections_raised TEXT,
                engagement_score REAL DEFAULT 0.0,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table recommendations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                reason TEXT,
                relevance_score REAL,
                accepted INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    # === INTENT DETECTION ===
    
    def detect_intent(self, message: str) -> tuple[UserIntent, float]:
        """Détecte l'intent d'un message"""
        message_lower = message.lower()
        
        # Check chaque intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            if score > 0:
                # Normalise score (max 3 patterns matchés = 100%)
                intent_scores[intent] = min(score / 3.0, 1.0)
        
        if not intent_scores:
            # Default: browsing
            return UserIntent.BROWSING, 0.3
        
        # Return meilleur score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]
    
    def analyze_objection(self, message: str) -> Optional[str]:
        """Identifie type d'objection"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["cher", "prix", "coût", "budget"]):
            return "trop_cher"
        
        if any(word in message_lower for word in ["qualité", "bien", "sûr", "doute"]):
            return "pas_sur_qualite"
        
        if any(word in message_lower for word in ["temps", "occupé", "busy", "plus tard"]):
            return "pas_le_temps"
        
        if any(word in message_lower for word in ["débutant", "commence", "nouveau", "jamais"]):
            return "debutant"
        
        return None
    
    # === CONVERSATION MANAGEMENT ===
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Crée nouvelle session"""
        import uuid
        session_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (session_id, user_id)
            VALUES (?, ?)
        """, (session_id, user_id))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[UserIntent] = None,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Ajoute message à conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO messages (
                session_id, role, content, intent, confidence, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            role,
            content,
            intent.value if intent else None,
            confidence,
            json.dumps(metadata) if metadata else None
        ))
        
        message_id = cursor.lastrowid
        
        # Update conversation
        cursor.execute("""
            UPDATE conversations
            SET last_message_at = ?,
                total_messages = total_messages + 1
            WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
        
        return ChatMessage(
            id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            confidence=confidence,
            metadata=metadata or {}
        )
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Récupère historique conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            msg = ChatMessage(
                id=row[0],
                session_id=row[1],
                role=row[2],
                content=row[3],
                intent=UserIntent(row[4]) if row[4] else None,
                confidence=row[5],
                timestamp=datetime.fromisoformat(row[6]),
                metadata=json.loads(row[7]) if row[7] else {}
            )
            messages.append(msg)
        
        conn.close()
        return list(reversed(messages))  # Plus ancien d'abord
    
    # === RECOMMENDATIONS ===
    
    def get_recommendations(
        self,
        user_profile: UserProfile,
        context: Optional[str] = None,
        max_results: int = 3
    ) -> List[Recommendation]:
        """Génère recommandations personnalisées"""
        recommendations = []
        
        # Simulate video database (à remplacer par vraie API)
        mock_videos = [
            {
                "id": "vid_001",
                "title": "Montage Vidéo Pro en 10 Minutes",
                "topics": ["editing", "tutorial"],
                "price": 15.0,
                "engagement": 8.5
            },
            {
                "id": "vid_002",
                "title": "Color Grading Cinéma - Guide Complet",
                "topics": ["color", "advanced"],
                "price": 25.0,
                "engagement": 9.2
            },
            {
                "id": "vid_003",
                "title": "Effets Spéciaux VFX - Débutant",
                "topics": ["vfx", "beginner"],
                "price": 12.0,
                "engagement": 7.8
            }
        ]
        
        # Score chaque vidéo
        for video in mock_videos:
            score = 0.5  # Base score
            reason_parts = []
            
            # Déjà vu?
            if video["id"] in user_profile.viewed_videos:
                continue
            
            # Déjà acheté?
            if video["id"] in user_profile.purchase_history:
                continue
            
            # Topics match
            matching_topics = set(video["topics"]) & set(user_profile.favorite_topics)
            if matching_topics:
                score += 0.3
                reason_parts.append(f"Tu aimes {', '.join(matching_topics)}")
            
            # Budget match
            if user_profile.budget_range:
                if user_profile.budget_range == "low" and video["price"] < 15:
                    score += 0.2
                    reason_parts.append("Dans ton budget")
                elif user_profile.budget_range == "high":
                    score += 0.1
            
            # Engagement score
            score += video["engagement"] / 100.0
            
            # Context bonus
            if context:
                context_lower = context.lower()
                if any(topic in context_lower for topic in video["topics"]):
                    score += 0.2
                    reason_parts.append("Correspond à ta recherche")
            
            if not reason_parts:
                reason_parts.append("Populaire dans la communauté")
            
            recommendations.append(Recommendation(
                video_id=video["id"],
                title=video["title"],
                reason=" + ".join(reason_parts),
                relevance_score=min(score, 1.0),
                price=video["price"],
                preview_available=True
            ))
        
        # Trie par score
        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return recommendations[:max_results]
    
    def log_recommendation(
        self,
        session_id: str,
        video_id: str,
        reason: str,
        relevance_score: float
    ):
        """Log recommandation pour analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO recommendations_log (
                session_id, video_id, reason, relevance_score
            ) VALUES (?, ?, ?, ?)
        """, (session_id, video_id, reason, relevance_score))
        
        conn.commit()
        conn.close()
    
    # === CHAT FLOW ===
    
    def generate_response(
        self,
        session_id: str,
        user_message: str,
        user_profile: UserProfile
    ) -> str:
        """Génère réponse du chatbot"""
        
        # Detect intent
        intent, confidence = self.detect_intent(user_message)
        
        # Log user message
        self.add_message(
            session_id=session_id,
            role="user",
            content=user_message,
            intent=intent,
            confidence=confidence
        )
        
        # Generate response based on intent
        if intent == UserIntent.READY_TO_BUY:
            response = self._handle_ready_to_buy(user_profile)
        
        elif intent == UserIntent.PRICE_CONCERN:
            response = self._handle_price_concern(user_message, user_profile)
        
        elif intent == UserIntent.OBJECTION:
            response = self._handle_objection(user_message)
        
        elif intent == UserIntent.COMPARISON:
            response = self._handle_comparison(user_profile)
        
        elif intent == UserIntent.TECHNICAL_QUESTION:
            response = self._handle_technical_question(user_message)
        
        else:  # BROWSING, INTERESTED
            response = self._handle_discovery(user_message, user_profile)
        
        # Log assistant response
        self.add_message(
            session_id=session_id,
            role="assistant",
            content=response,
            metadata={"intent_detected": intent.value, "confidence": confidence}
        )
        
        return response
    
    def _handle_ready_to_buy(self, user_profile: UserProfile) -> str:
        """Handle user prêt à acheter"""
        return """🔥 LETS GO!

Voici comment faire:

1️⃣ Choisis ta vidéo/bundle
2️⃣ Paiement sécurisé (carte ou PayPal)
3️⃣ Accès INSTANTANÉ

💳 Paiement 100% sécurisé
🔒 Garantie remboursé 30j
🎯 Support 7j/7

Tu veux que je te recommande LA meilleure vidéo pour toi?"""
    
    def _handle_price_concern(self, message: str, user_profile: UserProfile) -> str:
        """Handle inquiétude prix"""
        return """Je comprends! 💰

Voici le deal:
• 1 vidéo = 15€ (prix d'un McDo et Netflix combinés)
• Bundle 3 vidéos = 35€ au lieu de 45€ (-22%)
• Accès À VIE + updates gratuites

Et franchement: UNE SEULE technique peut te faire économiser 10h de galère. Ton temps vaut combien?

💡 Astuce: commence avec UNE vidéo pour tester. Si t'aimes pas → remboursement immédiat!

Quel sujet t'intéresse le plus?"""
    
    def _handle_objection(self, message: str) -> str:
        """Handle objection"""
        objection_type = self.analyze_objection(message)
        
        if objection_type and objection_type in self.objection_responses:
            return self.objection_responses[objection_type]["response"]
        
        # Objection générique
        return """Je comprends ton hésitation! 🤔

Laisse-moi te rassurer:
✅ +1500 clients satisfaits (4.8/5 ⭐)
✅ Garantie remboursé 30j SANS QUESTION
✅ Preview COMPLÈTE disponible
✅ Support direct avec moi

Qu'est-ce qui te fait hésiter exactement? Je peux t'aider! 💬"""
    
    def _handle_comparison(self, user_profile: UserProfile) -> str:
        """Handle comparaison"""
        return """Bonne question! 👌

Voici pourquoi mes vidéos:

🎯 **vs YouTube gratuit:**
   • Pas de blabla - straight to the point
   • Techniques PRO jamais partagées gratuitement
   • Fichiers projets inclus
   • Support personnalisé

💰 **vs Formations à 500€:**
   • Même qualité, 30x moins cher
   • Pas d'engagement mensuel
   • Accès à vie
   • Tu paies que ce qui t'intéresse

🔥 **vs Autres créateurs:**
   • Mon style unique (tu verras!)
   • Communauté ultra active
   • Updates régulières GRATUITES

Check les previews et compare toi-même! 😉"""
    
    def _handle_technical_question(self, message: str) -> str:
        """Handle question technique"""
        return """📋 Infos techniques:

**Format:** MP4 HD (1920x1080)
**Durée:** Variable (5-30min selon vidéo)
**Fichiers inclus:** Projets sources + assets
**Compatibilité:** Tous logiciels (Premiere, Final Cut, DaVinci...)

**Accès:**
• Streaming illimité
• Téléchargement possible
• Disponible sur tous devices

C'est quoi ta question exactement? Je peux détailler! 🎥"""
    
    def _handle_discovery(self, message: str, user_profile: UserProfile) -> str:
        """Handle phase discovery"""
        # Get recommendations
        recommendations = self.get_recommendations(user_profile, context=message, max_results=2)
        
        if not recommendations:
            return """Hey! 👋

Je peux t'aider à trouver LA vidéo parfaite pour toi.

Tu cherches quoi exactement?
• Montage/Editing?
• Color Grading?
• Effets spéciaux?
• Autre chose?

Dis-moi et je te trouve les meilleures! 🎯"""
        
        # Format recommendations
        reco_text = "\n\n".join([
            f"🎬 **{rec.title}**\n   → {rec.reason}\n   💰 {rec.price}€ | 🎬 Preview dispo"
            for rec in recommendations
        ])
        
        return f"""Yo! Je pense que tu vas ADORER ça:

{reco_text}

Tu veux que je te montre les previews? 👀"""


def main():
    """Test Consumer Chat System"""
    print("💬 Consumer Chat System - Tests\n")
    
    chat = ConsumerChatAI()
    
    # Create user profile
    profile = UserProfile(
        user_id="user_123",
        viewed_videos=["vid_004"],
        favorite_topics=["editing", "tutorial"],
        budget_range="medium",
        engagement_score=7.5
    )
    
    # Create session
    session_id = chat.create_session(user_id=profile.user_id)
    print(f"✅ Session créée: {session_id}\n")
    
    # Simulate conversation
    test_messages = [
        "Salut! Je cherche des tutos sur le montage vidéo",
        "C'est combien?",
        "C'est un peu cher non?",
        "OK je suis intéressé, comment je fais?"
    ]
    
    for i, user_msg in enumerate(test_messages, 1):
        print(f"{'='*60}")
        print(f"💬 User: {user_msg}")
        print(f"{'='*60}\n")
        
        # Get response
        response = chat.generate_response(session_id, user_msg, profile)
        print(f"🤖 Assistant:\n{response}\n")
        
        # Show intent detection
        intent, confidence = chat.detect_intent(user_msg)
        print(f"📊 Intent détecté: {intent.value} (confidence: {confidence:.0%})\n")
    
    # Show conversation stats
    history = chat.get_conversation_history(session_id)
    print(f"\n📊 Stats conversation:")
    print(f"   • Total messages: {len(history)}")
    print(f"   • Messages user: {sum(1 for m in history if m.role == 'user')}")
    print(f"   • Messages assistant: {sum(1 for m in history if m.role == 'assistant')}")
    
    print("\n✅ Consumer Chat System opérationnel!")


if __name__ == "__main__":
    main()
