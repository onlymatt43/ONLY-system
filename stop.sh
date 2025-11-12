#!/bin/bash
# Script d'arrêt complet du système ONLY

echo "🛑 Arrêt du système ONLY..."
echo ""

# Fonction pour arrêter un service
stop_service() {
    local name=$1
    local pidfile="logs/${name}.pid"
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🛑 Arrêt $name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            rm "$pidfile"
        else
            echo "⚠️  $name n'est pas en cours d'exécution"
            rm "$pidfile"
        fi
    else
        echo "⚠️  Pas de fichier PID pour $name"
    fi
}

# Arrêter tous les services
stop_service "Gateway"
stop_service "Curator-Bot"
stop_service "Narrator-AI"
stop_service "Builder-Bot"
stop_service "Publisher-AI"
stop_service "Sentinel-Dashboard"

# Nettoyer les processus Python restants sur les ports
echo ""
echo "🧹 Nettoyage des processus restants..."
for port in 5054 5055 5056 5057 5058 5059; do
    pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "   Arrêt du processus sur port $port (PID: $pid)"
        kill -9 "$pid" 2>/dev/null
    fi
done

echo ""
echo "✅ Tous les services sont arrêtés"
