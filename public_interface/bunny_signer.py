import os
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional

def get_secure_embed_url(
    library_id: int,
    video_id: str,
    security_key: Optional[str] = None,
    expires_in_hours: int = 2,
    autoplay: bool = True,
    expires_ts: Optional[int] = None
) -> str:
    """Generate secure Bunny Stream embed URL with token authentication"""
    
    # Use security key from parameter or environment
    key = security_key or os.environ.get('BUNNY_SECURITY_KEY')
    
    if not key:
        print("⚠️ BUNNY_SECURITY_KEY not configured, returning unsigned URL")
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay={'true' if autoplay else 'false'}"
    
    # Calculate expiration timestamp (allow deterministic override for tests)
    expires = int(expires_ts if expires_ts is not None else (datetime.now() + timedelta(hours=expires_in_hours)).timestamp())
    
    # Bunny official approach: use HMAC-SHA256 with the security key (secret)
    # over the canonical data in the format: library_id/video_id/expiration
    # This matches the Bunny docs which use slash-separated segments.
    message = f"{library_id}/{video_id}/{expires}".encode('utf-8')
    signature_hash = hmac.new(key.encode('utf-8'), message, hashlib.sha256).digest()
    # Base64 URL-safe without padding
    token = base64.urlsafe_b64encode(signature_hash).decode('utf-8').rstrip("=")
    
    # Build URL with token and expires parameters
    base_url = f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}"
    params = [
        f"token={token}",
        f"expires={expires}",
        f"autoplay={'true' if autoplay else 'false'}"
    ]
    
    signed_url = f"{base_url}?{'&'.join(params)}"
    
    # Do not log security sensitive info in production
    if os.environ.get('ENVIRONMENT') != 'production':
        print(f"✅ Signed URL generated (token length: {len(token)})")
    
    return signed_url


if __name__ == "__main__":
    # Test
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
