"""
Sales & Retention Engine API
Flask REST API pour FOMO, social proof, retention
"""

from flask import Flask, request, jsonify
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
from sales_engine import (
    SalesEngine, FOMOCampaign, SocialProof, RetentionCampaign,
    FOMOTechnique, SocialProofType, RetentionTrigger
)
from datetime import datetime
import os

app = Flask(__name__)
if CORS_AVAILABLE:
    CORS(app)

# Initialize engine
DB_PATH = os.getenv("SALES_DB_PATH", "sales_engine.db")
engine = SalesEngine(db_path=DB_PATH)


# === FOMO CAMPAIGNS ===

@app.route('/fomo/create', methods=['POST'])
def create_fomo():
    """Crée campagne FOMO"""
    data = request.json
    
    try:
        technique = FOMOTechnique(data.get('technique', 'time_limited'))
        campaign = engine.create_fomo_campaign(
            technique=technique,
            message=data['message'],
            duration_hours=data.get('duration_hours'),
            video_ids=data.get('video_ids', []),
            target_audience=data.get('target_audience', 'all'),
            urgency_level=data.get('urgency_level', 5)
        )
        
        return jsonify({
            "success": True,
            "campaign": {
                "id": campaign.id,
                "technique": campaign.technique.value,
                "message": campaign.get_countdown_message(),
                "urgency_level": campaign.urgency_level,
                "end_date": campaign.end_date.isoformat() if campaign.end_date else None
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/fomo/active', methods=['GET'])
def get_active_fomo():
    """Récupère campagnes FOMO actives"""
    audience = request.args.get('audience', 'all')
    
    campaigns = engine.get_active_fomo_campaigns(audience)
    
    return jsonify({
        "success": True,
        "campaigns": [
            {
                "id": c.id,
                "technique": c.technique.value,
                "message": c.get_countdown_message(),
                "urgency_level": c.urgency_level,
                "target_audience": c.target_audience,
                "video_ids": c.video_ids,
                "stats": {
                    "impressions": c.impressions,
                    "clicks": c.clicks,
                    "conversion_rate": round(c.conversion_rate * 100, 1)
                }
            }
            for c in campaigns
        ]
    })


@app.route('/fomo/track', methods=['POST'])
def track_fomo():
    """Track interaction FOMO"""
    data = request.json
    
    engine.track_fomo_interaction(
        campaign_id=data['campaign_id'],
        action=data.get('action', 'impression')  # impression, click
    )
    
    return jsonify({"success": True})


# === SOCIAL PROOF ===

@app.route('/proof/add', methods=['POST'])
def add_proof():
    """Ajoute social proof"""
    data = request.json
    
    try:
        proof_type = SocialProofType(data['proof_type'])
        proof = engine.add_social_proof(
            proof_type=proof_type,
            message=data.get('message', ''),
            value=data['value'],
            video_id=data.get('video_id'),
            source=data.get('source', 'homepage'),
            is_verified=data.get('is_verified', False)
        )
        
        return jsonify({
            "success": True,
            "proof": {
                "id": proof.id,
                "type": proof.proof_type.value,
                "formatted": proof.format_message(),
                "value": proof.value,
                "is_verified": proof.is_verified
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/proof/list', methods=['GET'])
def list_proofs():
    """Liste social proofs"""
    video_id = request.args.get('video_id')
    
    proofs = engine.get_social_proofs(video_id)
    
    return jsonify({
        "success": True,
        "proofs": [
            {
                "id": p.id,
                "type": p.proof_type.value,
                "formatted": p.format_message(),
                "value": p.value,
                "video_id": p.video_id,
                "source": p.source,
                "is_verified": p.is_verified
            }
            for p in proofs
        ]
    })


# === RETENTION CAMPAIGNS ===

@app.route('/retention/create', methods=['POST'])
def create_retention():
    """Crée campagne retention"""
    data = request.json
    
    try:
        trigger = RetentionTrigger(data['trigger'])
        campaign = engine.create_retention_campaign(
            trigger=trigger,
            name=data['name'],
            message_template=data['message_template'],
            delay_hours=data.get('delay_hours', 24),
            offer=data.get('offer'),
            discount_percentage=data.get('discount_percentage', 0),
            target_segment=data.get('target_segment', 'inactive')
        )
        
        return jsonify({
            "success": True,
            "campaign": {
                "id": campaign.id,
                "trigger": campaign.trigger.value,
                "name": campaign.name,
                "delay_hours": campaign.delay_hours,
                "discount": campaign.discount_percentage
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/retention/trigger', methods=['POST'])
def trigger_retention():
    """Déclenche événement retention"""
    data = request.json
    
    try:
        trigger_type = RetentionTrigger(data['trigger_type'])
        engine.trigger_retention_event(
            user_id=data['user_id'],
            trigger_type=trigger_type
        )
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/retention/pending', methods=['GET'])
def pending_retention():
    """Actions retention à envoyer"""
    actions = engine.get_pending_retention_actions()
    
    return jsonify({
        "success": True,
        "actions": actions,
        "count": len(actions)
    })


@app.route('/retention/mark-sent', methods=['POST'])
def mark_retention_sent():
    """Marque action comme envoyée"""
    data = request.json
    
    engine.mark_retention_action_sent(
        trigger_id=data['trigger_id'],
        converted=data.get('converted', False)
    )
    
    return jsonify({"success": True})


# === ANALYTICS ===

@app.route('/stats', methods=['GET'])
def get_stats():
    """Stats globales"""
    stats = engine.get_campaign_stats()
    
    return jsonify({
        "success": True,
        "stats": stats
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "sales-engine",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5072))
    app.run(host="0.0.0.0", port=port, debug=False)
