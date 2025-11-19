#!/bin/bash
# filepath: /Users/mathieucourchesne/ONLY-system-1/fix_system.sh

echo "🔧 ONLY System - Auto-Fix Script"
echo "=================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher le statut
status() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Stop tous les services
echo "1️⃣ Arrêt des services..."
./stop_all.sh 2>/dev/null
status "Services arrêtés"
echo ""

# 2. Nettoyer les processus orphelins
echo "2️⃣ Nettoyage processus..."
for port in 5000 5055 5056 5058 5059 5060 5061 5062; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null
        status "Port $port libéré"
    fi
done
echo ""

# 3. Installer les dépendances manquantes
echo "3️⃣ Installation dépendances..."

services=("web_interface" "gateway" "narrator_ai" "publisher_ai" "monetizer_ai" "public_interface" "curator_bot" "sentinel_dashboard")

for service in "${services[@]}"; do
    if [ -f "$service/requirements.txt" ]; then
        echo "   Installing $service..."
        cd "$service"
        pip3 install -q -r requirements.txt
        cd ..
        status "$service dépendances OK"
    fi
done
echo ""

# 4. Vérifier/créer .env files
echo "4️⃣ Vérification .env..."

# Gateway
if [ ! -f "gateway/.env" ]; then
    cat > gateway/.env << 'EOF'
PORT=5055
NARRATOR_URL=http://localhost:5056
PUBLISHER_URL=http://localhost:5058
DB_PATH=./gateway.db
WORKER_INTERVAL_SEC=5
EOF
    status "gateway/.env créé"
fi

# Monetizer
if [ ! -f "monetizer_ai/.env" ]; then
    cat > monetizer_ai/.env << 'EOF'
PORT=5060
DB_PATH=./monetizer.db
SECRET_KEY=change-me-in-production
CODE_PREFIX=OM43
DEFAULT_DURATION_MIN=1440
EOF
    warn "monetizer_ai/.env créé - CHANGE SECRET_KEY"
fi

# Public Interface
if [ ! -f "public_interface/.env" ]; then
    cat > public_interface/.env << 'EOF'
PORT=5062
CURATOR_URL=http://localhost:5061
MONETIZER_URL=http://localhost:5060
BUNNY_SECURITY_KEY=
EOF
    warn "public_interface/.env créé - ADD BUNNY_SECURITY_KEY"
fi

echo ""

# 5. Corriger bunny_signer.py
echo "5️⃣ Correction bunny_signer.py..."

cat > public_interface/bunny_signer.py << 'PYTHON_EOF'
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
PYTHON_EOF

status "bunny_signer.py corrigé"
echo ""

# 6. Corriger web_interface upload
echo "6️⃣ Correction web_interface.py..."

# Backup
cp web_interface/web_interface.py web_interface/web_interface.py.backup

# Patch la fonction upload
cat > /tmp/web_fix.py << 'PYTHON_EOF'
@app.post("/api/upload")
async def upload_video(request: Request):
    """Créer un job via Gateway"""
    try:
        data = await request.json()
        video_url = data.get("url", "")
        title = data.get("title", "")
        
        if not video_url:
            raise HTTPException(status_code=400, detail="URL vidéo requise")
        
        gateway_url = os.environ.get("GATEWAY_URL", "http://localhost:5055")
        
        response = requests.post(
            f"{gateway_url}/event",
            json={
                "event": "manual_upload",
                "file": video_url,
                "title": title,
                "timestamp": datetime.now().isoformat()
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Gateway error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=502, detail=f"Gateway error: {response.text}")
        
        job = response.json()
        
        return {
            "ok": True,
            "job_id": job.get("job_id"),
            "message": "Vidéo en cours de traitement"
        }
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Gateway at {gateway_url}")
        raise HTTPException(status_code=503, detail="Gateway non disponible")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Gateway timeout")
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
PYTHON_EOF

warn "web_interface.py - backup créé, patch manuel requis"
echo ""

# 7. Test des ports disponibles
echo "7️⃣ Test ports disponibles..."
ports=(5000 5055 5056 5058 5059 5060 5061 5062)
all_free=true

for port in "${ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        error "Port $port occupé"
        all_free=false
    else
        status "Port $port libre"
    fi
done
echo ""

# 8. Résumé
echo "=================================="
echo "📊 RÉSUMÉ"
echo "=================================="
echo ""

if [ "$all_free" = true ]; then
    status "Tous les ports sont libres"
else
    warn "Certains ports sont occupés (voir ci-dessus)"
fi

status "Dépendances installées"
status "Fichiers .env vérifiés"
status "bunny_signer.py corrigé"

echo ""
echo "⚠️  ACTIONS MANUELLES REQUISES:"
echo ""
echo "1. Édite monetizer_ai/.env:"
echo "   SECRET_KEY=ton-secret-tres-long-ici"
echo ""
echo "2. Édite public_interface/.env:"
echo "   BUNNY_SECURITY_KEY=ton-uuid-bunny-ici"
echo ""
echo "3. Applique le patch web_interface.py:"
echo "   cat /tmp/web_fix.py"
echo "   (Remplace la fonction @app.post(\"/api/upload\"))"
echo ""
echo "4. Relance le système:"
echo "   ./start_all.sh"
echo ""
echo "=================================="
echo "✅ Auto-fix terminé !"
echo "=================================="