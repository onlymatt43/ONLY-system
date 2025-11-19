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
    
    # Use security key from parameter or environment
    key = security_key or os.environ.get('BUNNY_SECURITY_KEY')
    
    if not key:
        print("⚠️ BUNNY_SECURITY_KEY not configured, returning unsigned URL")
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay={'true' if autoplay else 'false'}"
    
    # Calculate expiration timestamp
    expires = int((datetime.now() + timedelta(hours=expires_in_hours)).timestamp())
    
    # ✅ CORRECT FORMAT selon Bunny docs:
    # SHA256 hash de: library_id + security_key + expires + video_id (SANS séparateurs)
    signature_data = f"{library_id}{key}{expires}{video_id}"
    
    print(f"🔐 Signature data: library_id={library_id}, expires={expires}, video_id={video_id}")
    
    # Generate SHA256 hash (pas HMAC, juste SHA256)
    signature_hash = hashlib.sha256(signature_data.encode('utf-8')).digest()
    
    # Base64 encode (standard, pas URL-safe) et remove padding
    token = base64.urlsafe_b64encode(signature_hash).decode('utf-8')
    
    # Build URL with token and expires parameters
    base_url = f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}"
    params = [
        f"token={token}",
        f"expires={expires}",
        f"autoplay={'true' if autoplay else 'false'}"
    ]
    
    signed_url = f"{base_url}?{'&'.join(params)}"
    
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
