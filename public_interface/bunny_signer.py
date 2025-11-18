"""
Bunny Stream Signed URL Generator
Génère des tokens JWT pour les embeds sécurisés
"""

import os
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

# Security key from Bunny Dashboard → Library → Security → "Security Key"
BUNNY_SECURITY_KEY = os.getenv("BUNNY_SECURITY_KEY", "")

def generate_token(library_id: str, video_id: str, expires_in_seconds: int = 3600) -> str:
    """
    Génère un token signé pour Bunny Stream embed
    
    Args:
        library_id: ID de la library Bunny (389178)
        video_id: UUID de la vidéo
        expires_in_seconds: Durée validité (defaut: 1h)
    
    Returns:
        Token JWT signé
    """
    if not BUNNY_SECURITY_KEY:
        raise ValueError("BUNNY_SECURITY_KEY not configured")
    
    # Timestamp expiration
    expiration = int(time.time()) + expires_in_seconds
    
    # Paramètres du token
    token_data = f"{library_id}/{video_id}/{expiration}"
    
    # Signature HMAC-SHA256
    signature = hmac.new(
        BUNNY_SECURITY_KEY.encode(),
        token_data.encode(),
        hashlib.sha256
    ).digest()
    
    # Encode base64 URL-safe
    token = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    return token


def get_secure_embed_url(
    library_id: int,
    video_id: str,
    security_key: str = None,
    expires_in_hours: int = 2,
    autoplay: bool = True
) -> str:
    """
    Generate secure Bunny Stream embed URL with token authentication
    """
    
    # Use security key from parameter or environment
    key = security_key or os.environ.get('BUNNY_SECURITY_KEY')
    
    if not key:
        print("⚠️ BUNNY_SECURITY_KEY not configured, returning unsigned URL")
        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay={'true' if autoplay else 'false'}"
    
    # Calculate expiration timestamp
    expires = int((datetime.now() + timedelta(hours=expires_in_hours)).timestamp())
    
    # Create signature data
    signature_data = f"{library_id}{security_key}{expires}{video_id}"
    
    # Generate SHA256 hash
    signature_hash = hashlib.sha256(signature_data.encode('utf-8')).digest()
    
    # Base64 encode and make URL-safe
    token = base64.urlsafe_b64encode(signature_hash).decode('utf-8').rstrip('=')
    
    # Build URL
    base_url = f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}"
    params = [
        f"token={token}",
        f"expires={expires}",
        f"autoplay={'true' if autoplay else 'false'}"
    ]
    
    return f"{base_url}?{'&'.join(params)}"


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
        )
        print("✅ Secure URL generated:")
        print(url)
    except Exception as e:
        print(f"❌ Error: {e}")
