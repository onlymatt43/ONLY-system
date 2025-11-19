# filepath: /Users/mathieucourchesne/ONLY-system-1/public_interface/bunny_signer.py
import os
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

def get_secure_embed_url(
    library_id: int,
    video_id: str,
    security_key: str = None,
    expires_in_hours: int = 2,
    autoplay: bool = True
) -> str:
    """Generate secure Bunny Stream embed URL with token authentication"""
    
    key = security_key or os.environ.get('BUNNY_SECURITY_KEY')
    
    if not key:
        print("⚠️ BUNNY_SECURITY_KEY not configured, returning unsigned URL")
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay={'true' if autoplay else 'false'}"
    
    expires = int((datetime.now() + timedelta(hours=expires_in_hours)).timestamp())
    signature_data = f"{library_id}{key}{expires}{video_id}"
    signature_hash = hashlib.sha256(signature_data.encode('utf-8')).digest()
    token = base64.urlsafe_b64encode(signature_hash).decode('utf-8').rstrip('=')
    
    base_url = f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}"
    params = [
        f"token={token}",
        f"expires={expires}",
        f"autoplay={'true' if autoplay else 'false'}"
    ]
    
    return f"{base_url}?{'&'.join(params)}"

if __name__ == "__main__":
    try:
        url = get_secure_embed_url(
            library_id=389178,
            video_id="test-video-id",
            expires_in_hours=2
        )
        print("✅ Secure URL generated:")
        print(url)
    except Exception as e:
        print(f"❌ Error: {e}")
