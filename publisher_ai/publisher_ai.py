import os
import json
import smtplib
import requests
import pathlib
from email.mime.text import MIMEText
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from datetime import datetime

# YouTube imports
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

load_dotenv()

app = FastAPI(title="Publisher AI", version="1.1")

# ---------- Mail / Telegram ----------
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
NOTIFY_TO = os.getenv("NOTIFY_TO")

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID")


def send_email(subject: str, body: str):
    if not (SMTP_SERVER and SMTP_USER and SMTP_PASS and NOTIFY_TO):
        return False
    msg = MIMEText(body, "plain")
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_TO
    msg["Subject"] = subject
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, [NOTIFY_TO], msg.as_string())
    return True


def send_telegram(msg: str):
    if not (TG_TOKEN and TG_CHAT):
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT, "text": msg})
    return True


# ---------- X / Twitter (API v2) ----------
X_BEARER = os.getenv("X_BEARER_USER")
X_POST = os.getenv("X_API_POST", "https://api.twitter.com/2/tweets")


def post_to_x(text: str):
    if not X_BEARER:
        return {"ok": False, "skip": "no X token"}
    headers = {
        "Authorization": f"Bearer {X_BEARER}",
        "Content-Type": "application/json"
    }
    r = requests.post(X_POST, headers=headers, json={"text": text}, timeout=30)
    ok = r.status_code in (200, 201)
    return {
        "ok": ok,
        "status": r.status_code,
        "resp": r.json() if ok else r.text[:400]
    }


# ---------- Instagram Graph (Business) ----------
IG_USER_ID = os.getenv("IG_USER_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_BASE = os.getenv("IG_API_BASE", "https://graph.facebook.com/v19.0")


def ig_create_media(image_url: str = None, video_url: str = None, caption: str = ""):
    if not (IG_USER_ID and IG_TOKEN):
        return {"ok": False, "skip": "no IG creds"}
    
    endpoint = f"{IG_BASE}/{IG_USER_ID}/media"
    payload = {"caption": caption, "access_token": IG_TOKEN}
    
    if image_url:
        payload["image_url"] = image_url
    if video_url:
        payload["video_url"] = video_url
    
    r = requests.post(endpoint, data=payload, timeout=60)
    
    if r.status_code not in (200, 201):
        return {"ok": False, "status": r.status_code, "err": r.text[:400]}
    
    return {"ok": True, "id": r.json().get("id")}


def ig_publish_creation(creation_id: str):
    endpoint = f"{IG_BASE}/{IG_USER_ID}/media_publish"
    r = requests.post(
        endpoint,
        data={"creation_id": creation_id, "access_token": IG_TOKEN},
        timeout=60
    )
    
    if r.status_code not in (200, 201):
        return {"ok": False, "status": r.status_code, "err": r.text[:400]}
    
    return {"ok": True, "id": r.json().get("id")}


# ---------- YouTube Upload ----------
YT_CLIENT_SECRETS = os.getenv("YT_CLIENT_SECRETS", "./client_secret.json")
YT_CREDENTIALS = os.getenv("YT_CREDENTIALS", "./yt_token.json")
YT_PRIVACY = os.getenv("YT_DEFAULT_PRIVACY", "unlisted")
YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def yt_get_service():
    creds = None
    if os.path.exists(YT_CREDENTIALS):
        creds = Credentials.from_authorized_user_file(YT_CREDENTIALS, YT_SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request as GReq
            creds.refresh(GReq())
        else:
            if not os.path.exists(YT_CLIENT_SECRETS):
                raise RuntimeError("Missing YouTube client_secret.json")
            flow = InstalledAppFlow.from_client_secrets_file(
                YT_CLIENT_SECRETS, YT_SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(YT_CREDENTIALS, "w") as f:
            f.write(creds.to_json())
    
    return build("youtube", "v3", credentials=creds)


def yt_upload(video_path: str, title: str, description: str, privacy_status: str = None):
    svc = yt_get_service()
    privacy = privacy_status or YT_PRIVACY
    
    body = {
        "snippet": {
            "title": title[:95],
            "description": description[:4900],
            "categoryId": "22"
        },
        "status": {"privacyStatus": privacy}
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    req = svc.videos().insert(part="snippet,status", body=body, media_body=media)
    
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
    
    video_id = resp.get("id")
    return {
        "ok": True,
        "video_id": video_id,
        "watch": "https://youtu.be/" + video_id
    }


# ---------- API ----------
@app.post("/notify")
async def notify(req: Request):
    data = await req.json()
    title = data.get("title", "New content")
    link = data.get("link", "")
    msg = f"🎬 New episode: {title}\n{link}"
    
    em = send_email(f"New: {title}", msg)
    tg = send_telegram(msg)
    
    return {"ok": True, "email": em, "telegram": tg}


@app.post("/social/publish")
async def social_publish(req: Request):
    """Publie sur X, Instagram, YouTube"""
    data = await req.json()
    title = data.get("title", "")
    desc = data.get("description", "")
    link = data.get("link", "")
    caption = f"{title}\n{desc[:160]}\n{link}".strip()
    
    results = {}
    
    # X (tweet texte + lien)
    try:
        results["x"] = post_to_x(f"{title}\n{link}".strip())
    except Exception as e:
        results["x"] = {"ok": False, "err": str(e)[:200]}
    
    # Instagram (image OU vidéo via URL publique)
    try:
        ig_media = None
        if data.get("image_url"):
            ig_media = ig_create_media(image_url=data["image_url"], caption=caption)
        elif data.get("video_url"):
            ig_media = ig_create_media(video_url=data["video_url"], caption=caption)
        else:
            ig_media = {"ok": False, "skip": "no image_url/video_url"}
        
        if ig_media.get("ok"):
            results["instagram"] = ig_publish_creation(ig_media["id"])
        else:
            results["instagram"] = ig_media
    except Exception as e:
        results["instagram"] = {"ok": False, "err": str(e)[:200]}
    
    # YouTube (upload fichier local)
    try:
        local = data.get("local_video_path")
        if local and os.path.exists(local):
            results["youtube"] = yt_upload(local, title or "New Upload", desc or title, None)
        else:
            results["youtube"] = {"ok": False, "skip": "no local file"}
    except Exception as e:
        results["youtube"] = {"ok": False, "err": str(e)[:200]}
    
    return {"ok": True, "results": results}


@app.get("/")
def home():
    return {"status": "PublisherAI online"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "publisher_ai",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5058")))
