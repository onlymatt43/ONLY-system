#!/bin/bash

# 🚀 Démarre tous les services ONLY en arrière-plan
# Utilise tmux pour gérer les sessions

echo "🚀 Démarrage du système ONLY"
echo "============================="
echo ""

# Vérifier si tmux est installé
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux n'est pas installé. Installation..."
    brew install tmux
fi

# Nom de la session tmux
SESSION="only"

# Tuer la session existante si elle existe
tmux kill-session -t $SESSION 2>/dev/null

# Créer une nouvelle session
tmux new-session -d -s $SESSION -n "gateway"

# Fenêtre 1: Gateway
tmux send-keys -t $SESSION:0 "cd gateway && source venv/bin/activate 2>/dev/null || true && python3 gateway.py" C-m

# Fenêtre 2: Narrator AI
tmux new-window -t $SESSION -n "narrator"
tmux send-keys -t $SESSION:1 "cd narrator_ai && source venv/bin/activate 2>/dev/null || true && python3 narrator_ai.py" C-m

# Fenêtre 3: Publisher AI
tmux new-window -t $SESSION -n "publisher"
tmux send-keys -t $SESSION:2 "cd publisher_ai && source venv/bin/activate 2>/dev/null || true && python3 publisher_ai.py" C-m

# Fenêtre 4: Monetizer AI
tmux new-window -t $SESSION -n "monetizer"
tmux send-keys -t $SESSION:3 "cd monetizer_ai && source venv/bin/activate 2>/dev/null || true && python3 monetizer_ai.py" C-m

# Fenêtre 5: Web Interface
tmux new-window -t $SESSION -n "web"
tmux send-keys -t $SESSION:4 "cd web_interface && source venv/bin/activate 2>/dev/null || true && python3 web_interface.py" C-m

# Fenêtre 6: Sentinel Dashboard (optionnel)
tmux new-window -t $SESSION -n "sentinel"
tmux send-keys -t $SESSION:5 "cd sentinel_dashboard && source venv/bin/activate 2>/dev/null || true && python3 sentinel.py" C-m

echo "✅ Services démarrés en arrière-plan dans tmux"
echo ""
echo "📋 Commandes utiles :"
echo "  tmux attach -t only          # Attacher à la session"
echo "  tmux ls                      # Lister les sessions"
echo "  tmux kill-session -t only    # Arrêter tous les services"
echo ""
echo "🌐 URLs :"
echo "  Web Interface : http://localhost:5000"
echo "  Sentinel      : http://localhost:5059"
echo "  Gateway API   : http://localhost:5055"
echo ""
echo "⌨️  Navigation tmux :"
echo "  Ctrl+B puis D   # Détacher (services continuent)"
echo "  Ctrl+B puis [   # Scroll dans les logs"
echo "  Ctrl+B puis N   # Fenêtre suivante"
echo "  Ctrl+B puis P   # Fenêtre précédente"
echo ""
echo "Attends 5-10 secondes que les services démarrent..."
sleep 5

# Tester si les services sont prêts
echo ""
echo "🧪 Test de connectivité..."
curl -s http://localhost:5055/health > /dev/null && echo "  ✓ Gateway OK" || echo "  ⏳ Gateway démarrage..."
curl -s http://localhost:5056/health > /dev/null && echo "  ✓ Narrator OK" || echo "  ⏳ Narrator démarrage..."
curl -s http://localhost:5058/health > /dev/null && echo "  ✓ Publisher OK" || echo "  ⏳ Publisher démarrage..."
curl -s http://localhost:5060/health > /dev/null && echo "  ✓ Monetizer OK" || echo "  ⏳ Monetizer démarrage..."
curl -s http://localhost:5000/ > /dev/null && echo "  ✓ Web Interface OK" || echo "  ⏳ Web Interface démarrage..."
curl -s http://localhost:5059/ > /dev/null && echo "  ✓ Sentinel OK" || echo "  ⏳ Sentinel démarrage..."

echo ""
echo "🎉 Système ONLY prêt !"
echo "👉 Ouvre http://localhost:5000 dans ton navigateur"
