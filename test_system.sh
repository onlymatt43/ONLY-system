#!/bin/bash

# 🧪 Script de test complet ONLY
# Vérifie que tous les services répondent correctement

echo "🚀 Test du système ONLY"
echo "======================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour tester un endpoint
test_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url 2>/dev/null)
    
    if [ "$response" == "$expected_code" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        return 1
    fi
}

# Compteur de tests
total=0
passed=0

# Test 1: Gateway
echo "📦 Services Backend"
echo "-------------------"
test_service "Gateway Health" "http://localhost:5055/health"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

test_service "Gateway Jobs" "http://localhost:5055/jobs"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

# Test 2: Narrator AI
test_service "Narrator Health" "http://localhost:5056/health"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

# Test 3: Publisher AI
test_service "Publisher Health" "http://localhost:5058/health"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

# Test 4: Monetizer AI
test_service "Monetizer Health" "http://localhost:5060/health"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

test_service "Monetizer Tokens" "http://localhost:5060/tokens"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

# Test 5: Sentinel Dashboard
test_service "Sentinel Dashboard" "http://localhost:5059/"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

# Test 6: Web Interface
test_service "Web Interface Home" "http://localhost:5000/"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

test_service "Web Interface API Status" "http://localhost:5000/api/status"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

test_service "Web Interface API Jobs" "http://localhost:5000/api/jobs"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

# Test 7: Créer un job test
echo -n "Testing Job Creation... "
response=$(curl -s -X POST http://localhost:5055/event \
    -H "Content-Type: application/json" \
    -d '{
        "event": "test_upload",
        "file": "/tmp/test_video.mp4",
        "timestamp": "2025-01-01T00:00:00Z"
    }' 2>/dev/null)

if echo "$response" | grep -q "job_id"; then
    echo -e "${GREEN}✓ OK${NC}"
    total=$((total + 1))
    passed=$((passed + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    total=$((total + 1))
fi

# Test 8: Créer un token
echo -n "Testing Token Creation... "
response=$(curl -s -X POST http://localhost:5060/mint \
    -H "Content-Type: application/json" \
    -d '{
        "video_id": "test123",
        "duration_minutes": 60
    }' 2>/dev/null)

if echo "$response" | grep -q "token"; then
    echo -e "${GREEN}✓ OK${NC}"
    total=$((total + 1))
    passed=$((passed + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    total=$((total + 1))
fi

# Test 9: Curator Bot
test_service "Curator Bot" "http://localhost:5061/health"
total=$((total + 1))
[ $? -eq 0 ] && passed=$((passed + 1))

# Résumé
echo ""
echo "========================="
echo "📊 Résumé des tests"
echo "========================="
echo "Total: $total tests"
echo -e "Passed: ${GREEN}$passed${NC}"
echo -e "Failed: ${RED}$((total - passed))${NC}"
echo ""

if [ $passed -eq $total ]; then
    echo -e "${GREEN}✓ Tous les tests passent ! Système prêt pour Render 🚀${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Certains tests ont échoué. Vérifie les services.${NC}"
    echo ""
    echo "Aide au débogage :"
    echo "- Vérifie que tous les services sont lancés"
    echo "- Regarde les logs de chaque service"
    echo "- Assure-toi que les ports ne sont pas déjà utilisés"
    exit 1
fi
