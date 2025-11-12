#!/bin/bash

# 🛑 Arrête tous les services ONLY

echo "🛑 Arrêt du système ONLY"
echo "========================"
echo ""

SESSION="only"

# Vérifier si la session tmux existe
if tmux has-session -t $SESSION 2>/dev/null; then
    tmux kill-session -t $SESSION
    echo "✅ Tous les services ont été arrêtés"
else
    echo "⚠️  Aucune session tmux 'only' trouvée"
    echo ""
    echo "Recherche de processus Python ONLY..."
    
    # Chercher et tuer les processus Python des services ONLY
    pkill -f "python.*gateway.py" && echo "  ✓ Gateway arrêté"
    pkill -f "python.*narrator_ai.py" && echo "  ✓ Narrator arrêté"
    pkill -f "python.*publisher_ai.py" && echo "  ✓ Publisher arrêté"
    pkill -f "python.*monetizer_ai.py" && echo "  ✓ Monetizer arrêté"
    pkill -f "python.*web_interface.py" && echo "  ✓ Web Interface arrêté"
    pkill -f "python.*sentinel.py" && echo "  ✓ Sentinel arrêté"
    pkill -f "python.*curator_bot.py" && echo "  ✓ Curator arrêté"
fi

echo ""
echo "🧹 Vérification des ports..."

# Vérifier que les ports sont libérés
for port in 5000 5055 5056 5058 5059 5060; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "  ⚠️  Port $port encore occupé"
        lsof -ti:$port | xargs kill -9 2>/dev/null
    else
        echo "  ✓ Port $port libre"
    fi
done

echo ""
echo "✅ Système ONLY complètement arrêté"
