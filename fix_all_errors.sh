#!/bin/bash

echo "🔧 ONLY System - Correction Automatique des Erreurs"
echo "======================================================"

# 1. Gateway - Ajoute /health
if ! grep -q '@app.get("/health")' gateway/gateway.py; then
    echo "📝 Ajout /health à Gateway..."
    # Insertion après app = FastAPI()
    sed -i '' '/app = FastAPI()/a\
\
@app.get("/health")\
async def health():\
    """Health check endpoint"""\
    return {\
        "status": "healthy",\
        "service": "gateway",\
        "port": PORT,\
        "timestamp": datetime.now().isoformat()\
    }\
' gateway/gateway.py
    echo "✅ Gateway /health ajouté"
fi

# 2. Vérifie que datetime est importé partout
for file in gateway/gateway.py web_interface/web_interface.py curator_bot/curator_bot.py; do
    if ! grep -q "from datetime import datetime" "$file"; then
        echo "⚠️ datetime manquant dans $file"
    fi
done

echo ""
echo "✅ Corrections terminées !"
echo ""
echo "📝 Actions manuelles restantes:"
echo "1. Applique les corrections ci-dessus dans chaque fichier"
echo "2. Teste avec: ./test_system.sh"
echo "3. Push sur GitHub: git add . && git commit -m 'Fix: All health endpoints + imports' && git push"
