#!/bin/bash

echo "=============================="
echo "🧪 Test Style Learner API"
echo "=============================="

BASE_URL="http://localhost:5070"

echo ""
echo "1️⃣ Training Style Learner..."
curl -s -X POST "$BASE_URL/style/train" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [
      {"text": "🔥 OK LES GARS\n\nJai découvert un truc INSANE pour éditer 10x plus vite\n\nRegarde ça 👇\n\n#tutorial #editing", "platform": "twitter"},
      {"text": "💡 Cette technique va te choquer\n\nPersonne nen parle mais cest GAME CHANGER\n\nVideo complète: only.com/123", "platform": "twitter"},
      {"text": "YO! 👀\n\nJai passé 5h sur ce projet...\n\nLe résultat? FOU 🔥\n\nCheck la vidéo #insane", "platform": "twitter"},
      {"text": "😱 TU DOIS VOIR ÇA\n\nLa méthode que tous les pros utilisent\n\nTu vas kiffer 💯", "platform": "twitter"},
      {"text": "🎯 Comment jai fait ça en 10 minutes?\n\nLaisse-moi te montrer\n\nCest plus simple que tu penses 💎", "platform": "twitter"}
    ]
  }' | python3 -m json.tool

echo ""
echo ""
echo "2️⃣ Analyzing Style..."
curl -s -X POST "$BASE_URL/style/analyze" | python3 -m json.tool | head -40

echo ""
echo ""
echo "3️⃣ Getting Style Profile..."
curl -s -X GET "$BASE_URL/style/profile" | python3 -m json.tool | head -30

echo ""
echo ""
echo "4️⃣ Generating Post for video 135..."
curl -s -X POST "$BASE_URL/style/generate" \
  -H "Content-Type: application/json" \
  -d '{"video_id": "135", "platform": "twitter"}' | python3 -m json.tool

echo ""
echo ""
echo "✅ Tests complets!"
