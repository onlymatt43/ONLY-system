"""
Blog & Homepage Engine API
Flask REST API pour blog generation, SEO, homepage
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from blog_engine import (
    BlogEngine, BlogPost, HomepageSection, SEOMetadata,
    ContentType, SEOPriority
)
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Initialize engine
DB_PATH = os.getenv("BLOG_DB_PATH", "blog_engine.db")
engine = BlogEngine(db_path=DB_PATH)


# === BLOG POST GENERATION ===

@app.route('/blog/generate', methods=['POST'])
def generate_blog():
    """Génère blog post à partir d'une vidéo"""
    data = request.json
    
    try:
        post = engine.generate_blog_post(
            video_id=data['video_id'],
            video_title=data['video_title'],
            video_description=data.get('video_description', ''),
            category=data.get('category', 'tutorial'),
            keywords=data.get('keywords')
        )
        
        return jsonify({
            "success": True,
            "post": {
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "intro": post.intro,
                "body": post.body,
                "conclusion": post.conclusion,
                "meta_description": post.meta_description,
                "keywords": post.keywords,
                "category": post.category,
                "read_time_minutes": post.read_time_minutes,
                "seo_score": round(post.seo_score, 1),
                "published": post.published,
                "url": f"/blog/{post.slug}"
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/blog/publish/<int:post_id>', methods=['POST'])
def publish_blog(post_id):
    """Publie un blog post"""
    # TODO: Implémenter publish logic
    return jsonify({
        "success": True,
        "message": "Post published",
        "post_id": post_id
    })


@app.route('/blog/list', methods=['GET'])
def list_blogs():
    """Liste blog posts"""
    # TODO: Implémenter query avec filters
    return jsonify({
        "success": True,
        "posts": []
    })


# === HOMEPAGE SECTIONS ===

@app.route('/homepage/section/create', methods=['POST'])
def create_section():
    """Crée section homepage"""
    data = request.json
    
    try:
        section = engine.create_homepage_section(
            section_type=data['section_type'],
            title=data['title'],
            video_ids=data['video_ids'],
            subtitle=data.get('subtitle', ''),
            display_order=data.get('display_order', 0),
            auto_update=data.get('auto_update', True)
        )
        
        return jsonify({
            "success": True,
            "section": {
                "id": section.id,
                "type": section.section_type,
                "title": section.title,
                "subtitle": section.subtitle,
                "video_count": len(section.video_ids),
                "auto_update": section.auto_update
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/homepage/sections', methods=['GET'])
def get_sections():
    """Récupère toutes sections homepage"""
    sections = engine.get_homepage_sections()
    
    return jsonify({
        "success": True,
        "sections": [
            {
                "id": s.id,
                "type": s.section_type,
                "title": s.title,
                "subtitle": s.subtitle,
                "video_ids": s.video_ids,
                "display_order": s.display_order,
                "is_active": s.is_active,
                "auto_update": s.auto_update
            }
            for s in sections
        ]
    })


@app.route('/homepage/trending/update', methods=['POST'])
def update_trending():
    """Met à jour section Trending"""
    data = request.json
    engagement_data = data['engagement_data']  # List of {video_id, engagement_score}
    
    engine.update_trending_section(engagement_data)
    
    return jsonify({
        "success": True,
        "message": "Trending section updated"
    })


# === SEO METADATA ===

@app.route('/seo/generate', methods=['POST'])
def generate_seo():
    """Génère métadonnées SEO"""
    data = request.json
    
    try:
        metadata = engine.generate_seo_metadata(
            page_type=data['page_type'],
            page_id=data['page_id'],
            title=data['title'],
            description=data['description'],
            keywords=data.get('keywords', []),
            image_url=data.get('image_url', '')
        )
        
        return jsonify({
            "success": True,
            "metadata": {
                "title": metadata.title,
                "description": metadata.description,
                "keywords": metadata.keywords,
                "og_title": metadata.og_title,
                "og_description": metadata.og_description,
                "og_image": metadata.og_image,
                "canonical_url": metadata.canonical_url,
                "schema_markup": metadata.schema_markup
            }
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# === ANALYTICS ===

@app.route('/analytics/track', methods=['POST'])
def track_view():
    """Track page view"""
    data = request.json
    
    engine.track_page_view(
        content_type=data['content_type'],
        content_id=data['content_id'],
        time_on_page=data.get('time_on_page', 0)
    )
    
    return jsonify({"success": True})


@app.route('/analytics/top-content', methods=['GET'])
def top_content():
    """Top contenu par vues"""
    limit = int(request.args.get('limit', 10))
    
    results = engine.get_top_content(limit)
    
    return jsonify({
        "success": True,
        "top_content": results
    })


# === HEALTH ===

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "blog-engine",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5074))
    app.run(host="0.0.0.0", port=port, debug=False)
