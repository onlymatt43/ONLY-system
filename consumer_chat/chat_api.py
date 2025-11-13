"""
Consumer Chat System API
Flask REST API pour AI chat, recommendations, objections
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from consumer_chat import (
    ConsumerChatAI, UserProfile, UserIntent,
    ConversationStage
)
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Initialize chat AI
DB_PATH = os.getenv("CHAT_DB_PATH", "consumer_chat.db")
chat_ai = ConsumerChatAI(db_path=DB_PATH)


# === SESSION MANAGEMENT ===

@app.route('/chat/session/create', methods=['POST'])
def create_session():
    """Crée nouvelle session chat"""
    data = request.json
    user_id = data.get('user_id')
    
    session_id = chat_ai.create_session(user_id)
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "greeting": "Hey! 👋 Je peux t'aider à trouver LA vidéo parfaite pour toi. C'est quoi ton projet?"
    })


@app.route('/chat/message', methods=['POST'])
def send_message():
    """Envoie message et reçoit réponse"""
    data = request.json
    
    session_id = data['session_id']
    user_message = data['message']
    
    # User profile (optionnel, peut être stocké en session)
    profile_data = data.get('profile', {})
    profile = UserProfile(
        user_id=profile_data.get('user_id', 'guest'),
        viewed_videos=profile_data.get('viewed_videos', []),
        favorite_topics=profile_data.get('favorite_topics', []),
        budget_range=profile_data.get('budget_range'),
        purchase_history=profile_data.get('purchase_history', []),
        engagement_score=profile_data.get('engagement_score', 5.0)
    )
    
    # Generate response
    response = chat_ai.generate_response(session_id, user_message, profile)
    
    # Detect intent for analytics
    intent, confidence = chat_ai.detect_intent(user_message)
    
    return jsonify({
        "success": True,
        "response": response,
        "intent": {
            "detected": intent.value,
            "confidence": round(confidence * 100, 0)
        }
    })


@app.route('/chat/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Récupère historique conversation"""
    limit = int(request.args.get('limit', 10))
    
    history = chat_ai.get_conversation_history(session_id, limit)
    
    return jsonify({
        "success": True,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "intent": m.intent.value if m.intent else None,
                "confidence": round(m.confidence * 100, 0) if m.confidence else None,
                "timestamp": m.timestamp.isoformat()
            }
            for m in history
        ]
    })


# === INTENT DETECTION ===

@app.route('/chat/detect-intent', methods=['POST'])
def detect_intent_endpoint():
    """Détecte intent d'un message"""
    data = request.json
    message = data['message']
    
    intent, confidence = chat_ai.detect_intent(message)
    
    return jsonify({
        "success": True,
        "intent": intent.value,
        "confidence": round(confidence * 100, 0)
    })


# === RECOMMENDATIONS ===

@app.route('/chat/recommend', methods=['POST'])
def get_recommendations():
    """Génère recommandations personnalisées"""
    data = request.json
    
    # Build user profile
    profile = UserProfile(
        user_id=data.get('user_id', 'guest'),
        viewed_videos=data.get('viewed_videos', []),
        favorite_topics=data.get('favorite_topics', []),
        budget_range=data.get('budget_range'),
        purchase_history=data.get('purchase_history', [])
    )
    
    context = data.get('context')
    max_results = data.get('max_results', 3)
    
    recommendations = chat_ai.get_recommendations(profile, context, max_results)
    
    return jsonify({
        "success": True,
        "recommendations": [
            {
                "video_id": rec.video_id,
                "title": rec.title,
                "reason": rec.reason,
                "relevance_score": round(rec.relevance_score * 100, 0),
                "price": rec.price,
                "preview_available": rec.preview_available
            }
            for rec in recommendations
        ]
    })


@app.route('/chat/recommend/log', methods=['POST'])
def log_recommendation():
    """Log recommandation pour analytics"""
    data = request.json
    
    chat_ai.log_recommendation(
        session_id=data['session_id'],
        video_id=data['video_id'],
        reason=data.get('reason', ''),
        relevance_score=data.get('relevance_score', 0.5)
    )
    
    return jsonify({"success": True})


# === OBJECTION HANDLING ===

@app.route('/chat/analyze-objection', methods=['POST'])
def analyze_objection():
    """Analyse type d'objection"""
    data = request.json
    message = data['message']
    
    objection_type = chat_ai.analyze_objection(message)
    
    if objection_type and objection_type in chat_ai.objection_responses:
        response_data = chat_ai.objection_responses[objection_type]
        return jsonify({
            "success": True,
            "objection_type": objection_type,
            "suggested_response": response_data['response'],
            "offer": response_data.get('offer')
        })
    
    return jsonify({
        "success": True,
        "objection_type": None,
        "suggested_response": None
    })


# === HEALTH ===

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "consumer-chat",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5073))
    app.run(host="0.0.0.0", port=port, debug=False)
