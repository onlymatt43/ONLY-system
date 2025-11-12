#!/bin/bash

# 🚀 Script de déploiement rapide sur Render
# Ce script prépare ton code pour le déploiement web

echo "🚀 Préparation pour déploiement Render"
echo "======================================"
echo ""

# Étape 1 : Vérifier que git est initialisé
if [ ! -d .git ]; then
    echo "📦 Initialisation Git..."
    git init
    git add .
    git commit -m "Initial commit - ONLY system ready for web deployment"
    echo "✅ Git initialisé"
else
    echo "✅ Git déjà initialisé"
fi

# Étape 2 : Vérifier .gitignore
if [ -f .gitignore ]; then
    echo "✅ .gitignore présent"
else
    echo "⚠️  .gitignore manquant (mais ce n'est pas bloquant)"
fi

# Étape 3 : Status Git
echo ""
echo "📊 Status Git :"
git status --short

# Étape 4 : Instructions
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PRÊT POUR LE DÉPLOIEMENT WEB !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 PROCHAINES ÉTAPES (déploiement web) :"
echo ""
echo "1️⃣  Crée un repo GitHub :"
echo "   → Va sur https://github.com/new"
echo "   → Nom : ONLY-system"
echo "   → Public ou Private (ton choix)"
echo "   → NE PAS ajouter README/gitignore (déjà présents)"
echo ""
echo "2️⃣  Copie la commande GitHub te donne :"
echo '   git remote add origin https://github.com/TON_USERNAME/ONLY-system.git'
echo '   git branch -M main'
echo '   git push -u origin main'
echo ""
echo "3️⃣  Va sur Render.com :"
echo "   → https://dashboard.render.com"
echo "   → Sign up / Login (gratuit)"
echo "   → Connect ton compte GitHub"
echo ""
echo "4️⃣  Crée les 5 Web Services :"
echo "   → Suis RENDER_CHECKLIST.md (guide complet)"
echo "   → OU suis les étapes ci-dessous (résumé)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 RÉSUMÉ RENDER (5 services à créer) :"
echo ""
echo "Service 1/5 : only-web (PUBLIC)"
echo "  Root Directory: web_interface"
echo "  Build: pip install -r requirements.txt"
echo "  Start: uvicorn web_interface:app --host 0.0.0.0 --port \$PORT"
echo ""
echo "Service 2/5 : only-gateway"
echo "  Root Directory: gateway"
echo "  Build: pip install -r requirements.txt"
echo "  Start: python gateway.py"
echo "  + Disk: /data (1GB)"
echo ""
echo "Service 3/5 : only-narrator"
echo "  Root Directory: narrator_ai"
echo "  Build: pip install -r requirements.txt"
echo "  Start: python narrator_ai.py"
echo ""
echo "Service 4/5 : only-publisher"
echo "  Root Directory: publisher_ai"
echo "  Build: pip install -r requirements.txt"
echo "  Start: python publisher_ai.py"
echo ""
echo "Service 5/5 : only-monetizer"
echo "  Root Directory: monetizer_ai"
echo "  Build: pip install -r requirements.txt"
echo "  Start: python monetizer_ai.py"
echo "  + Disk: /data (1GB)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏱️  Temps estimé : 30-45 minutes (première fois)"
echo "💰 Coût : GRATUIT (avec limitations) ou \$35/mois (production)"
echo ""
echo "📖 Guide détaillé : cat RENDER_CHECKLIST.md"
echo ""
