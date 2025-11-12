#!/bin/bash
# Script de démarrage complet du système ONLY

echo "🎬 Démarrage du système ONLY..."
echo ""

# Fonction pour vérifier si un port est déjà utilisé
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $1 déjà utilisé"
        return 1
    fi
    return 0
}

# Vérification des ports
echo "🔍 Vérification des ports..."
check_port 5054 || exit 1
check_port 5055 || exit 1
check_port 5056 || exit 1
check_port 5057 || exit 1
check_port 5058 || exit 1
check_port 5059 || exit 1
echo "✅ Tous les ports sont disponibles"
echo ""

# Fonction pour démarrer un service
start_service() {
    local name=$1
    local dir=$2
    local port=$3
    local script=$4
    
    echo "🚀 Démarrage $name (port $port)..."
    cd "$dir" || exit 1
    
    if [ ! -f ".env" ]; then
        echo "⚠️  Copie de .env.example vers .env"
        cp .env.example .env
    fi
    
    python3 "$script" > "../logs/${name}.log" 2>&1 &
    echo $! > "../logs/${name}.pid"
    
    cd - > /dev/null
    sleep 1
}

# Créer le dossier logs
mkdir -p logs

# Démarrer les services dans l'ordre
start_service "Gateway" "gateway" 5055 "gateway.py"
sleep 2  # Laisser le Gateway démarrer en premier

start_service "Curator-Bot" "curator_bot" 5054 "curator_bot.py"
start_service "Narrator-AI" "narrator_ai" 5056 "narrator_ai.py"
start_service "Builder-Bot" "builder_bot" 5057 "builder_bot.py"
start_service "Publisher-AI" "publisher_ai" 5058 "publisher_ai.py"
start_service "Sentinel-Dashboard" "sentinel_dashboard" 5059 "sentinel.py"

echo ""
echo "✅ Tous les services sont démarrés !"
echo ""
echo "📊 Dashboard : http://localhost:5059"
echo "🚦 Gateway   : http://localhost:5055"
echo ""
echo "📝 Logs dans le dossier ./logs/"
echo ""
echo "Pour arrêter tous les services : ./stop.sh"
