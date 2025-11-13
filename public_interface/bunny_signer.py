"""
Bunny Stream Signed URL Generator
Génère des tokens JWT pour les embeds sécurisés
"""

import os
import time
import hmac
import hashlib
import base64
from typing import Optional

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


def get_secure_embed_url(library_id: str, video_id: str, autoplay: bool = True, 
                         muted: bool = False, expires_in: int = 3600) -> str:
    """
    Génère URL d'embed sécurisée avec token
    
    Args:
        library_id: ID library (389178)
        video_id: UUID vidéo
        autoplay: Lecture auto
        muted: Muet
        expires_in: Durée validité token (secondes)
    
    Returns:
        URL complète avec token
    """
    token = generate_token(library_id, video_id, expires_in)
    expiration = int(time.time()) + expires_in
    
    # Base URL
    url = f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}"
    
    # Query params
    params = [
        f"token={token}",
        f"expires={expiration}",
        f"autoplay={'true' if autoplay else 'false'}",
        f"muted={'true' if muted else 'false'}",
        "loop=false",
        "preload=true"
    ]
    
    return f"{url}?{'&'.join(params)}"


if __name__ == "__main__":
    # Test
    test_url = get_secure_embed_url(
        library_id="389178",
        video_id="d8f84503-7a71-4535-8069-6f84cc6d1b6e",
        autoplay=True,
        expires_in=3600
    )
    
    print("🔒 Secure Bunny Embed URL:")
    print(test_url)
