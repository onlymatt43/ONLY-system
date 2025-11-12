#!/bin/bash
# Script de test du système ONLY

echo "🧪 Test du système ONLY..."
echo ""

# Fonction pour tester un service
test_service() {
    local name=$1
    local url=$2
    
    echo -n "Testing $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" --connect-timeout 3)
    
    if [ "$response" = "200" ]; then
        echo "✅ OK ($response)"
        return 0
    else
        echo "❌ FAIL ($response)"
        return 1
    fi
}

# Tester tous les services
echo "🔍 Vérification des services..."
test_service "Gateway" "http://localhost:5055/"
test_service "Curator Bot" "http://localhost:5054/"
test_service "Narrator AI" "http://localhost:5056/"
test_service "Builder Bot" "http://localhost:5057/"
test_service "Publisher AI" "http://localhost:5058/"
test_service "Sentinel Dashboard" "http://localhost:5059/"

echo ""
echo "🎬 Test d'intégration : simulation d'une nouvelle vidéo"
echo ""

# Créer un fichier de test (vide)
mkdir -p test_videos
touch test_videos/test_video.mp4

# Envoyer un événement au Gateway
response=$(curl -s -X POST "http://localhost:5055/event" \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"new_video\",
    \"file\": \"$(pwd)/test_videos/test_video.mp4\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }")

echo "Gateway response:"
echo "$response" | python3 -m json.tool

echo ""
echo "📊 Vérifier le dashboard : http://localhost:5059"
echo ""
echo "✅ Test terminé"
