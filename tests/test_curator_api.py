import os
import json
from fastapi.testclient import TestClient
import tempfile

import curator_bot.curator_bot as curator


def setup_temp_db(tmp_path):
    dbfile = tmp_path / "curator_test.db"
    curator.DB_PATH = str(dbfile)
    # Ensure DB initialized
    curator.init_db()
    return str(dbfile)


def test_get_video_not_found(tmp_path):
    # Fresh DB -> no videos
    setup_temp_db(tmp_path)

    client = TestClient(curator.app)
    r = client.get("/videos/1")
    assert r.status_code == 404
    data = r.json()
    assert "detail" in data
    assert data["detail"]["error"].startswith("Video 1 not found")


def test_get_video_exists(tmp_path):
    setup_temp_db(tmp_path)

    # Insert a fake bunny video via the sync helper
    fake = {
        "guid": "test-guid-xyz",
        "title": "Test Video",
        "length": 5,
        "thumbnailFileName": "thumb.jpg"
    }

    video_id = curator.sync_video_from_bunny(fake, library_type="private")

    client = TestClient(curator.app)
    r = client.get(f"/videos/{video_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == video_id
    assert data["bunny_video_id"] == "test-guid-xyz"
    # views should exist and default to 0
    assert isinstance(data.get("view_count", 0), int)
