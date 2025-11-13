"""
Content Brain AI - API Service
Analyse vidéos et génère insights marketing
"""

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from video_analyzer import VideoAnalyzer, BatchVideoAnalyzer
from dataclasses import asdict

load_dotenv()

# Config
PORT = int(os.getenv("PORT", 5070))
CURATOR_URL = os.getenv("CURATOR_URL", "http://localhost:5061")

# Flask app
app = Flask(__name__)

# Initialize analyzers
video_analyzer = VideoAnalyzer(curator_url=CURATOR_URL)
batch_analyzer = BatchVideoAnalyzer(analyzer=video_analyzer)


# ==================== ROUTES ====================

@app.route("/", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        "service": "Content Brain AI",
        "version": "1.0",
        "status": "running",
        "curator_url": CURATOR_URL
    })


@app.route("/analyze/<video_id>", methods=["POST"])
def analyze_video(video_id: str):
    """
    Analyse une vidéo spécifique
    
    POST /analyze/123
    
    Returns:
        VideoInsights complet
    """
    try:
        insights = video_analyzer.analyze_video(video_id)
        
        return jsonify({
            "ok": True,
            "video_id": video_id,
            "insights": asdict(insights)
        })
        
    except ValueError as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 404
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500


@app.route("/analyze/batch", methods=["POST"])
def analyze_batch():
    """
    Analyse multiple vidéos
    
    POST /analyze/batch
    Body: {
        "library": "public|private|all",
        "limit": 10
    }
    
    Returns:
        Liste de VideoInsights
    """
    data = request.json or {}
    
    library_type = data.get("library", "all")
    limit = data.get("limit", None)
    
    if limit:
        limit = int(limit)
    
    try:
        insights_list = batch_analyzer.analyze_library(
            library_type=library_type,
            limit=limit
        )
        
        return jsonify({
            "ok": True,
            "count": len(insights_list),
            "library": library_type,
            "insights": [asdict(ins) for ins in insights_list]
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Batch analysis failed: {str(e)}"
        }), 500


@app.route("/top-performers", methods=["GET"])
def get_top_performers():
    """
    Retourne top vidéos par métrique
    
    GET /top-performers?metric=engagement&limit=10&library=all
    
    Args:
        metric: engagement|viral_potential|twitter|instagram|facebook|linkedin|bluesky
        limit: nombre de résultats (default 10)
        library: public|private|all (default all)
    
    Returns:
        Top N VideoInsights triés
    """
    metric = request.args.get("metric", "engagement")
    limit = int(request.args.get("limit", 10))
    library_type = request.args.get("library", "all")
    
    try:
        # Analyse toutes les vidéos
        insights_list = batch_analyzer.analyze_library(library_type=library_type)
        
        # Trie par métrique
        top_insights = batch_analyzer.get_top_performers(
            insights_list=insights_list,
            metric=metric,
            limit=limit
        )
        
        return jsonify({
            "ok": True,
            "metric": metric,
            "count": len(top_insights),
            "top_performers": [asdict(ins) for ins in top_insights]
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Failed to get top performers: {str(e)}"
        }), 500


@app.route("/preview/<video_id>/<platform>", methods=["GET"])
def get_optimal_preview(video_id: str, platform: str):
    """
    Retourne segment preview optimal pour plateforme
    
    GET /preview/123/twitter
    
    Args:
        video_id: ID vidéo
        platform: twitter|instagram|facebook|linkedin|bluesky
    
    Returns:
        Meilleur segment preview avec start, end, duration
    """
    
    valid_platforms = ["twitter", "instagram", "facebook", "linkedin", "bluesky"]
    
    if platform not in valid_platforms:
        return jsonify({
            "ok": False,
            "error": f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
        }), 400
    
    try:
        # Analyse vidéo
        insights = video_analyzer.analyze_video(video_id)
        
        # Récupère meilleur segment
        segment = video_analyzer.get_optimal_preview_for_platform(insights, platform)
        
        if not segment:
            return jsonify({
                "ok": False,
                "error": "No preview segment found for this platform"
            }), 404
        
        return jsonify({
            "ok": True,
            "video_id": video_id,
            "platform": platform,
            "preview_segment": segment,
            "platform_fit_score": insights.platform_fit.get(platform, 0)
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/hooks/<video_id>", methods=["GET"])
def get_hooks(video_id: str):
    """
    Retourne hooks suggérés pour une vidéo
    
    GET /hooks/123
    
    Returns:
        Liste de hooks accrocheurs
    """
    try:
        insights = video_analyzer.analyze_video(video_id)
        
        return jsonify({
            "ok": True,
            "video_id": video_id,
            "hooks": insights.suggested_hooks,
            "engagement_score": insights.engagement_score,
            "viral_potential": insights.viral_potential
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/stats", methods=["GET"])
def get_stats():
    """
    Statistiques globales du catalogue vidéo
    
    GET /stats?library=all
    
    Returns:
        Stats agrégées
    """
    library_type = request.args.get("library", "all")
    
    try:
        insights_list = batch_analyzer.analyze_library(library_type=library_type)
        
        if not insights_list:
            return jsonify({
                "ok": True,
                "count": 0,
                "message": "No videos to analyze"
            })
        
        # Calcule moyennes
        avg_engagement = sum(i.engagement_score for i in insights_list) / len(insights_list)
        avg_viral = sum(i.viral_potential for i in insights_list) / len(insights_list)
        
        # Platform fit moyen
        platform_avg = {}
        for platform in ["twitter", "instagram", "facebook", "linkedin", "bluesky"]:
            scores = [i.platform_fit.get(platform, 0) for i in insights_list]
            platform_avg[platform] = sum(scores) / len(scores) if scores else 0
        
        # Content types distribution
        content_types = {}
        for insight in insights_list:
            ct = insight.content_type
            content_types[ct] = content_types.get(ct, 0) + 1
        
        # Energy levels distribution
        energy_levels = {}
        for insight in insights_list:
            energy = insight.energy_level
            energy_levels[energy] = energy_levels.get(energy, 0) + 1
        
        return jsonify({
            "ok": True,
            "library": library_type,
            "total_videos": len(insights_list),
            "averages": {
                "engagement_score": round(avg_engagement, 1),
                "viral_potential": round(avg_viral, 1),
                "platform_fit": {k: round(v, 1) for k, v in platform_avg.items()}
            },
            "content_types": content_types,
            "energy_levels": energy_levels
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 Content Brain AI - Video Analyzer")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Curator URL: {CURATOR_URL}")
    print("=" * 60)
    
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True
    )
