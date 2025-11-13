"""
Admin Dashboard - Marketing System Control Center
Interface web pour gérer FOMO, Chat, Blog, Analytics
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sales_engine.sales_engine import SalesEngine, FOMOTechnique, SocialProofType, RetentionTrigger
from consumer_chat.consumer_chat import ConsumerChatAI, UserIntent, UserProfile
from blog_engine.blog_engine import BlogEngine

app = Flask(__name__)

# Initialize engines
sales_engine = SalesEngine("../sales_engine/sales_engine.db")
chat_ai = ConsumerChatAI("../consumer_chat/consumer_chat.db")
blog_engine = BlogEngine("../blog_engine/blog_engine.db")


# ===== HOME / OVERVIEW =====

@app.route('/')
def index():
    """Dashboard home - overview de tout"""
    
    # Stats globales
    sales_stats = sales_engine.get_campaign_stats()
    top_content = blog_engine.get_top_content(limit=5)
    
    return render_template('index.html',
                         sales_stats=sales_stats,
                         top_content=top_content)


# ===== FOMO CAMPAIGNS =====

@app.route('/fomo')
def fomo_campaigns():
    """Liste des campagnes FOMO"""
    campaigns = sales_engine.get_active_fomo_campaigns()
    return render_template('fomo.html', campaigns=campaigns)


@app.route('/fomo/create', methods=['GET', 'POST'])
def fomo_create():
    """Créer campagne FOMO"""
    if request.method == 'POST':
        data = request.form
        
        campaign = sales_engine.create_fomo_campaign(
            technique=FOMOTechnique(data['technique']),
            message=data['message'],
            duration_hours=int(data.get('duration_hours', 24)) if data.get('duration_hours') else None,
            target_audience=data.get('target_audience', 'all'),
            urgency_level=int(data.get('urgency_level', 5))
        )
        
        return redirect(url_for('fomo_campaigns'))
    
    # GET: show form
    techniques = [t.value for t in FOMOTechnique]
    return render_template('fomo_create.html', techniques=techniques)


@app.route('/api/fomo/<int:campaign_id>/stats')
def fomo_stats(campaign_id):
    """Stats d'une campagne FOMO (pour live updates)"""
    campaigns = sales_engine.get_active_fomo_campaigns()
    campaign = next((c for c in campaigns if c.id == campaign_id), None)
    
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    
    return jsonify({
        "id": campaign.id,
        "impressions": campaign.impressions,
        "clicks": campaign.clicks,
        "conversion_rate": round(campaign.conversion_rate * 100, 1),
        "countdown_message": campaign.get_countdown_message(),
        "is_expired": campaign.is_expired()
    })


# ===== SOCIAL PROOF =====

@app.route('/social-proof')
def social_proof_list():
    """Liste des preuves sociales"""
    proofs = sales_engine.get_social_proofs()
    return render_template('social_proof.html', proofs=proofs)


@app.route('/social-proof/create', methods=['POST'])
def social_proof_create():
    """Créer preuve sociale"""
    data = request.form
    
    proof = sales_engine.add_social_proof(
        proof_type=SocialProofType(data['proof_type']),
        message=data['message'],
        value=float(data['value']),
        video_id=data.get('video_id'),
        source=data.get('source', 'homepage'),
        is_verified=data.get('is_verified') == 'on'
    )
    
    return redirect(url_for('social_proof_list'))


# ===== CONSUMER CHAT =====

@app.route('/chat')
def chat_sessions():
    """Liste des conversations chat"""
    # Get recent sessions from DB
    import sqlite3
    conn = sqlite3.connect("../consumer_chat/consumer_chat.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, user_id, stage, started_at, total_messages, converted
        FROM conversations
        ORDER BY last_message_at DESC
        LIMIT 50
    """)
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "session_id": row[0],
            "user_id": row[1] or "Anonymous",
            "stage": row[2],
            "started_at": row[3],
            "total_messages": row[4],
            "converted": bool(row[5])
        })
    
    conn.close()
    
    return render_template('chat.html', sessions=sessions)


@app.route('/chat/<session_id>')
def chat_detail(session_id):
    """Détails d'une conversation"""
    messages = chat_ai.get_conversation_history(session_id, limit=100)
    
    return render_template('chat_detail.html',
                         session_id=session_id,
                         messages=messages)


@app.route('/api/chat/test', methods=['POST'])
def chat_test():
    """Test du chatbot"""
    data = request.json
    message = data.get('message', '')
    
    # Create test profile
    profile = UserProfile(
        user_id="test_user",
        favorite_topics=["editing", "tutorial"],
        budget_range="medium"
    )
    
    # Create or get session
    session_id = data.get('session_id')
    if not session_id:
        session_id = chat_ai.create_session(user_id="test_user")
    
    # Generate response
    response = chat_ai.generate_response(session_id, message, profile)
    intent, confidence = chat_ai.detect_intent(message)
    
    return jsonify({
        "session_id": session_id,
        "response": response,
        "intent": intent.value,
        "confidence": round(confidence * 100, 1)
    })


# ===== BLOG MANAGER =====

@app.route('/blog')
def blog_posts():
    """Liste des blog posts"""
    import sqlite3
    conn = sqlite3.connect("../blog_engine/blog_engine.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, slug, category, seo_score, published, view_count, created_at
        FROM blog_posts
        ORDER BY created_at DESC
    """)
    
    posts = []
    for row in cursor.fetchall():
        posts.append({
            "id": row[0],
            "title": row[1],
            "slug": row[2],
            "category": row[3],
            "seo_score": row[4],
            "published": bool(row[5]),
            "view_count": row[6],
            "created_at": row[7]
        })
    
    conn.close()
    
    return render_template('blog.html', posts=posts)


@app.route('/blog/generate', methods=['POST'])
def blog_generate():
    """Générer nouveau blog post"""
    data = request.form
    
    post = blog_engine.generate_blog_post(
        video_id=data['video_id'],
        video_title=data['video_title'],
        video_description=data['video_description'],
        category=data.get('category', 'tutorial'),
        keywords=data.get('keywords', '').split(',') if data.get('keywords') else None
    )
    
    return redirect(url_for('blog_posts'))


@app.route('/blog/<int:post_id>/publish', methods=['POST'])
def blog_publish(post_id):
    """Publier/dépublier un post"""
    import sqlite3
    from datetime import datetime
    
    conn = sqlite3.connect("../blog_engine/blog_engine.db")
    cursor = conn.cursor()
    
    # Toggle published status
    cursor.execute("""
        UPDATE blog_posts
        SET published = CASE WHEN published = 0 THEN 1 ELSE 0 END,
            published_at = CASE WHEN published = 0 THEN ? ELSE published_at END
        WHERE id = ?
    """, (datetime.now().isoformat(), post_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('blog_posts'))


# ===== HOMEPAGE SECTIONS =====

@app.route('/homepage')
def homepage_sections():
    """Gérer sections homepage"""
    sections = blog_engine.get_homepage_sections()
    return render_template('homepage.html', sections=sections)


@app.route('/homepage/update-trending', methods=['POST'])
def homepage_update_trending():
    """Update section Trending"""
    # Mock engagement data (à remplacer par vraies données)
    engagement_data = [
        {"video_id": f"vid_{i}", "engagement_score": 9.5 - i*0.3}
        for i in range(10)
    ]
    
    blog_engine.update_trending_section(engagement_data)
    
    return redirect(url_for('homepage_sections'))


# ===== ANALYTICS =====

@app.route('/analytics')
def analytics():
    """Dashboard analytics global"""
    
    # Sales stats
    sales_stats = sales_engine.get_campaign_stats()
    
    # Blog stats
    top_content = blog_engine.get_top_content(limit=10)
    
    # Chat stats (mock for now)
    chat_stats = {
        "total_sessions": 42,
        "avg_messages_per_session": 5.3,
        "conversion_rate": 12.5
    }
    
    return render_template('analytics.html',
                         sales_stats=sales_stats,
                         top_content=top_content,
                         chat_stats=chat_stats)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5080))
    app.run(host='0.0.0.0', port=port, debug=True)
