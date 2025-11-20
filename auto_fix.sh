#!/bin/bash

echo "🔧 ONLY System - Auto-Fix Script"
echo "=================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Créer .env global
echo "1️⃣ Création .env global..."
cat > .env << 'EOF'
# filepath: /Users/mathieucourchesne/ONLY-system-1/.env
ENVIRONMENT=local

# Services URLs (LOCAL)
CURATOR_URL=http://localhost:5061
MONETIZER_URL=http://localhost:5060
PUBLIC_URL=http://localhost:5062
GATEWAY_URL=http://localhost:5055

# Bunny Stream (Private Library 389178)
BUNNY_SECURITY_KEY=453f0507-2f2c-4155-95bd-31a2fdd3610c
BUNNY_PRIVATE_API_KEY=9bf388e8-181a-4740-bf90bc96c622-3394-4591
BUNNY_PRIVATE_LIBRARY_ID=389178
BUNNY_PRIVATE_CDN_HOSTNAME=vz-a3ab0733-842.b-cdn.net

# Bunny Stream (Public Library 420867)
BUNNY_PUBLIC_API_KEY=5eb42e83-6fe9-48fb-b08c5656f422-3033-490a
BUNNY_PUBLIC_LIBRARY_ID=420867
BUNNY_PUBLIC_CDN_HOSTNAME=vz-9cf89254-609.b-cdn.net

# Turso Database (Monetizer)
TURSO_DATABASE_URL=libsql://only-tokens-onlymatt43.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjMwMDA4ODEsImlkIjoiMDcwYzdkOGEtZGUwZC00OGExLWI5NmMtNjlkN2U5MDkxODYzIiwicmlkIjoiOGQyNWI5M2QtOTJhMy00MzgxLWJhN2ItZjM3MGFhYmUxZDc2In0.y8jY7sYrNg2q88su0IK8RcVo0pqDgGjqEfneuMEptWfylVCgAqJv-X1e9L3hrzpz_IYTmjNbs4uJGiJdE7CWAg

# Security
SECRET_KEY=0mO2mPJISGYEf00nnvwvGfdT2D9LilVYcz29cdpIDbeF2odFK5z-JAXsNx1bYMjPYwUAhWDQ067Mlo-9zi038g
CODE_PREFIX=OM43
EOF

echo -e "${GREEN}✅${NC} .env global créé"

# 2. Ajouter /health à Gateway
echo ""
echo "2️⃣ Ajout /health endpoint à Gateway..."

if grep -q '@app.get("/health")' gateway/gateway.py; then
    echo -e "${GREEN}✅${NC} Gateway /health déjà présent"
else
    # Backup
    cp gateway/gateway.py gateway/gateway.py.backup
    
    # Ajoute /health après les imports
    python3 << 'PYTHON'
with open("gateway/gateway.py", "r") as f:
    lines = f.readlines()

# Trouve où insérer (après app = FastAPI())
insert_pos = 0
for i, line in enumerate(lines):
    if "app = FastAPI()" in line:
        insert_pos = i + 1
        break

# Insère /health endpoint
health_code = '''
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gateway",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }

'''

lines.insert(insert_pos, health_code)

with open("gateway/gateway.py", "w") as f:
    f.writelines(lines)
PYTHON
    
    echo -e "${GREEN}✅${NC} /health ajouté à Gateway"
fi

# 3. Ajouter /health à Narrator
echo ""
echo "3️⃣ Ajout /health endpoint à Narrator..."

if grep -q '@app.get("/health")' narrator_ai/narrator_ai.py; then
    echo -e "${GREEN}✅${NC} Narrator /health déjà présent"
else
    cp narrator_ai/narrator_ai.py narrator_ai/narrator_ai.py.backup
    
    python3 << 'PYTHON'
with open("narrator_ai/narrator_ai.py", "r") as f:
    lines = f.readlines()

insert_pos = 0
for i, line in enumerate(lines):
    if "app = FastAPI()" in line:
        insert_pos = i + 1
        break

health_code = '''
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "narrator_ai",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }

'''

lines.insert(insert_pos, health_code)

with open("narrator_ai/narrator_ai.py", "w") as f:
    f.writelines(lines)
PYTHON
    
    echo -e "${GREEN}✅${NC} /health ajouté à Narrator"
fi

# 4. Ajouter /health à Publisher
echo ""
echo "4️⃣ Ajout /health endpoint à Publisher..."

if grep -q '@app.get("/health")' publisher_ai/publisher_ai.py; then
    echo -e "${GREEN}✅${NC} Publisher /health déjà présent"
else
    cp publisher_ai/publisher_ai.py publisher_ai/publisher_ai.py.backup
    
    python3 << 'PYTHON'
with open("publisher_ai/publisher_ai.py", "r") as f:
    lines = f.readlines()

insert_pos = 0
for i, line in enumerate(lines):
    if "app = FastAPI()" in line:
        insert_pos = i + 1
        break

health_code = '''
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "publisher_ai",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }

'''

lines.insert(insert_pos, health_code)

with open("publisher_ai/publisher_ai.py", "w") as f:
    f.writelines(lines)
PYTHON
    
    echo -e "${GREEN}✅${NC} /health ajouté à Publisher"
fi

# 5. Rendre le script exécutable
chmod +x auto_fix.sh

echo ""
echo "=================================="
echo -e "${GREEN}✅ Auto-fix terminé !${NC}"
echo "=================================="
echo ""
echo -e "${YELLOW}📝 ACTIONS MANUELLES RESTANTES:${NC}"
echo ""
echo "1️⃣ Sur Bunny Dashboard (https://panel.bunny.net):"
echo "   - Library 389178 → Security"
echo "   - Allowed Referrers: only-public.onrender.com, localhost"
echo "   - Désactive Token Authentication (temporaire pour tests)"
echo ""
echo "2️⃣ Sur Render Dashboard (https://dashboard.render.com):"
echo "   - Service only-public → Environment"
echo "   - Ajoute: BUNNY_SECURITY_KEY=453f0507-2f2c-4155-95bd-31a2fdd3610c"
echo "   - Save → Auto-redeploy (2-3 min)"
echo ""
echo "3️⃣ Relance le système local:"
echo "   ${GREEN}./stop_all.sh && ./start_all.sh${NC}"
echo ""
echo "4️⃣ Teste:"
echo "   ${GREEN}./test_system.sh${NC}"
echo ""
echo "🎉 Après ces étapes, ton système devrait être 100% fonctionnel !"
