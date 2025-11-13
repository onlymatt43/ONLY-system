"""
Content Scheduler API - REST endpoints pour scheduling automatisé
"""

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta
from content_scheduler import (
    ContentScheduler, Platform, ScheduleStatus, RetentionStrategy,
    ScheduledPost
)
from dataclasses import asdict
import requests

load_dotenv()

# Config
PORT = int(os.getenv("PORT", 5071))
CONTENT_BRAIN_URL = os.getenv("CONTENT_BRAIN_URL", "http://localhost:5070")
DB_PATH = os.getenv("DB_PATH", "./scheduler.db")

# Flask app
app = Flask(__name__)

# Initialize scheduler
scheduler = ContentScheduler(db_path=DB_PATH)


# ==================== ROUTES ====================

@app.route("/", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        "service": "Content Scheduler",
        "version": "1.0",
        "status": "running",
        "content_brain_url": CONTENT_BRAIN_URL
    })


@app.route("/schedule/create", methods=["POST"])
def create_schedule():
    """
    Crée schedule pour une vidéo avec auto-génération du post
    
    POST /schedule/create
    Body: {
        "video_id": "123",
        "platform": "twitter",
        "scheduled_time": "2025-11-15T18:00:00Z" (optional),
        "strategy": "regular" (optional)
    }
    
    Returns:
        ScheduledPost créé
    """
    data = request.json or {}
    
    video_id = data.get("video_id")
    platform_str = data.get("platform", "twitter")
    scheduled_time_str = data.get("scheduled_time")
    strategy_str = data.get("strategy", "regular")
    
    if not video_id:
        return jsonify({
            "ok": False,
            "error": "video_id required"
        }), 400
    
    # Validate platform
    try:
        platform = Platform(platform_str)
    except ValueError:
        return jsonify({
            "ok": False,
            "error": f"Invalid platform. Must be one of: {[p.value for p in Platform]}"
        }), 400
    
    # Validate strategy
    try:
        strategy = RetentionStrategy(strategy_str)
    except ValueError:
        return jsonify({
            "ok": False,
            "error": f"Invalid strategy. Must be one of: {[s.value for s in RetentionStrategy]}"
        }), 400
    
    # Parse scheduled_time
    scheduled_time = None
    if scheduled_time_str:
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        except:
            return jsonify({
                "ok": False,
                "error": "Invalid scheduled_time format. Use ISO format."
            }), 400
    
    try:
        # Generate post content via Content Brain Style Learner
        style_response = requests.post(
            f"{CONTENT_BRAIN_URL}/style/generate",
            json={
                "video_id": video_id,
                "platform": platform_str
            },
            timeout=30
        )
        
        if style_response.status_code != 200:
            return jsonify({
                "ok": False,
                "error": "Failed to generate post content. Is Style Learner trained?"
            }), 500
        
        style_data = style_response.json()
        generated_content = style_data.get("generated_post", "")
        style_match_score = style_data.get("style_match_score", 0.0)
        
        # Schedule post
        post = scheduler.schedule_post(
            video_id=video_id,
            platform=platform,
            generated_content=generated_content,
            style_match_score=style_match_score,
            scheduled_time=scheduled_time,
            strategy=strategy
        )
        
        return jsonify({
            "ok": True,
            "scheduled_post": asdict(post),
            "message": "Post scheduled successfully"
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "ok": False,
            "error": f"Content Brain connection failed: {str(e)}"
        }), 500
    
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/schedule/series", methods=["POST"])
def create_series():
    """
    Crée série de posts avec stratégie retention
    
    POST /schedule/series
    Body: {
        "video_ids": ["123", "124", "125"],
        "platform": "instagram",
        "strategy": "cliffhanger",
        "series_name": "Epic Tutorial Series",
        "start_date": "2025-11-15T10:00:00Z"
    }
    
    Returns:
        Liste ScheduledPosts créés
    """
    data = request.json or {}
    
    video_ids = data.get("video_ids", [])
    platform_str = data.get("platform", "twitter")
    strategy_str = data.get("strategy", "cliffhanger")
    series_name = data.get("series_name", "Unnamed Series")
    start_date_str = data.get("start_date")
    
    if not video_ids:
        return jsonify({
            "ok": False,
            "error": "video_ids required (array)"
        }), 400
    
    if not start_date_str:
        return jsonify({
            "ok": False,
            "error": "start_date required (ISO format)"
        }), 400
    
    # Validate
    try:
        platform = Platform(platform_str)
        strategy = RetentionStrategy(strategy_str)
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
    except ValueError as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400
    
    try:
        # Schedule series
        posts = scheduler.schedule_series(
            video_ids=video_ids,
            platform=platform,
            strategy=strategy,
            series_name=series_name,
            start_date=start_date
        )
        
        return jsonify({
            "ok": True,
            "series_name": series_name,
            "strategy": strategy_str,
            "posts_count": len(posts),
            "scheduled_posts": [asdict(p) for p in posts]
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/schedule/list", methods=["GET"])
def list_scheduled():
    """
    Liste posts programmés avec filtres
    
    GET /schedule/list?platform=twitter&status=scheduled&limit=50
    
    Args:
        platform: twitter|instagram|facebook|linkedin|bluesky (optional)
        status: scheduled|paused|published|failed|cancelled (optional)
        limit: nombre max (default 50)
    
    Returns:
        Liste ScheduledPosts
    """
    platform_str = request.args.get("platform")
    status_str = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    
    # Parse filters
    platform = None
    if platform_str:
        try:
            platform = Platform(platform_str)
        except ValueError:
            return jsonify({
                "ok": False,
                "error": f"Invalid platform: {platform_str}"
            }), 400
    
    status = None
    if status_str:
        try:
            status = ScheduleStatus(status_str)
        except ValueError:
            return jsonify({
                "ok": False,
                "error": f"Invalid status: {status_str}"
            }), 400
    
    try:
        posts = scheduler.get_scheduled_posts(
            platform=platform,
            status=status,
            limit=limit
        )
        
        return jsonify({
            "ok": True,
            "count": len(posts),
            "scheduled_posts": [asdict(p) for p in posts]
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/schedule/pause/<int:post_id>", methods=["POST"])
def pause_schedule(post_id: int):
    """
    Pause un post programmé
    
    POST /schedule/pause/123
    
    Returns:
        Confirmation
    """
    try:
        success = scheduler.pause_post(post_id)
        
        if success:
            return jsonify({
                "ok": True,
                "post_id": post_id,
                "message": "Post paused successfully"
            })
        else:
            return jsonify({
                "ok": False,
                "error": "Post not found or already paused"
            }), 404
            
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/schedule/resume/<int:post_id>", methods=["POST"])
def resume_schedule(post_id: int):
    """
    Resume un post pausé
    
    POST /schedule/resume/123
    
    Returns:
        Confirmation
    """
    try:
        success = scheduler.resume_post(post_id)
        
        if success:
            return jsonify({
                "ok": True,
                "post_id": post_id,
                "message": "Post resumed successfully"
            })
        else:
            return jsonify({
                "ok": False,
                "error": "Post not found or not paused"
            }), 404
            
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/schedule/cancel/<int:post_id>", methods=["POST"])
def cancel_schedule(post_id: int):
    """
    Annule un post
    
    POST /schedule/cancel/123
    
    Returns:
        Confirmation
    """
    try:
        success = scheduler.cancel_post(post_id)
        
        if success:
            return jsonify({
                "ok": True,
                "post_id": post_id,
                "message": "Post cancelled successfully"
            })
        else:
            return jsonify({
                "ok": False,
                "error": "Post not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/schedule/calendar/<platform>", methods=["GET"])
def get_calendar(platform: str):
    """
    Récupère calendrier pour platform
    
    GET /schedule/calendar/twitter
    
    Returns:
        ScheduleCalendar avec optimal hours, next slot
    """
    try:
        platform_enum = Platform(platform)
    except ValueError:
        return jsonify({
            "ok": False,
            "error": f"Invalid platform: {platform}"
        }), 400
    
    try:
        calendar = scheduler.get_calendar(platform_enum)
        
        return jsonify({
            "ok": True,
            "calendar": asdict(calendar)
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/schedule/analytics", methods=["GET"])
def get_analytics():
    """
    Récupère métriques retention globales
    
    GET /schedule/analytics
    
    Returns:
        RetentionMetrics
    """
    try:
        metrics = scheduler.get_retention_metrics()
        
        return jsonify({
            "ok": True,
            "metrics": asdict(metrics)
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 70)
    print("📅 Content Scheduler API")
    print("=" * 70)
    print(f"Port: {PORT}")
    print(f"Content Brain URL: {CONTENT_BRAIN_URL}")
    print(f"Database: {DB_PATH}")
    print("\n📊 Endpoints disponibles:")
    print("  POST /schedule/create")
    print("  POST /schedule/series")
    print("  GET  /schedule/list")
    print("  POST /schedule/pause/<post_id>")
    print("  POST /schedule/resume/<post_id>")
    print("  POST /schedule/cancel/<post_id>")
    print("  GET  /schedule/calendar/<platform>")
    print("  GET  /schedule/analytics")
    print("=" * 70)
    
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True
    )
