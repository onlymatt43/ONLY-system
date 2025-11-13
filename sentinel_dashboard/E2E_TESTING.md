# 🧪 Sentinel E2E Testing

Tests automatiques bout-en-bout pour détecter les bugs frontend invisibles aux tests serveur.

## Qu'est-ce que ça teste ?

### Tests Critiques
1. **Video Playback** 🎥
   - Vérifie que la page `/watch/{video_id}` charge
   - Vérifie que le `<video>` element existe
   - Vérifie que la source vidéo est définie (pas vide)
   - Vérifie que l'URL est HTTPS + format .m3u8
   - Vérifie que HLS.js est chargé
   - **Aurait détecté le bug `video.video_id` immédiatement**

2. **API Consistency** 🔌
   - Vérifie que Curator Bot répond
   - Vérifie que les champs requis existent (`video_url`, `bunny_video_id`, etc.)
   - Vérifie que `video_url` est bien formé
   - Détecte les désynchronisations API/Frontend

3. **Homepage Load** 🏠
   - Vérifie que la page d'accueil charge
   - Vérifie que les vidéos s'affichent
   - Vérifie que le titre existe

4. **Search Functionality** 🔍
   - Vérifie que la recherche est présente
   - Vérifie qu'on peut taper dedans
   - Vérifie que les résultats s'affichent

## Installation

```bash
cd sentinel_dashboard

# Installe Playwright
pip install -r e2e_requirements.txt

# Installe les navigateurs (Chromium pour headless)
playwright install chromium
```

## Utilisation

### Lancer les tests manuellement

```bash
python e2e_tester.py
```

Output:
```
🧪 Starting E2E Tests...
============================================================

[1/4] Testing API consistency...
  ✅ PASS (234ms)

[2/4] Testing homepage...
  ✅ PASS (1876ms)

[3/4] Testing video playback...
  ✅ PASS (2341ms)

[4/4] Testing search...
  ✅ PASS (1523ms)

============================================================
📊 Results: 4/4 tests passed
✅ All tests passed!
```

### Via Sentinel Dashboard (API)

```bash
curl http://localhost:10000/api/e2e/test
```

Retourne:
```json
{
  "summary": {
    "passed": 4,
    "failed": 0,
    "total": 4,
    "success_rate": 100.0
  },
  "results": {
    "video_playback": {
      "passed": true,
      "duration_ms": 2341,
      "screenshot_path": "./e2e_screenshots/video_playback_121_success.png"
    },
    ...
  }
}
```

## Screenshots

Quand un test **échoue**, Playwright prend automatiquement un screenshot:
- `e2e_screenshots/video_playback_121_error.png` - ce que l'utilisateur voit
- `e2e_screenshots/homepage_load_error.png`
- etc.

## Intégration avec Sentinel

Sentinel peut lancer ces tests automatiquement:

### Option 1: Tests périodiques (toutes les 5 minutes)
```python
# Dans sentinel2.py monitoring_loop()
if E2E_AVAILABLE and check_count % 10 == 0:  # Tous les 10 cycles
    e2e_results = tester.run_all_tests()
    if not all(r.passed for r in e2e_results.values()):
        create_incident("public_interface", "E2E tests failed", "CRITICAL")
```

### Option 2: Tests on-demand via Dashboard
Bouton "🧪 Run E2E Tests" dans le dashboard Sentinel qui appelle `/api/e2e/test`

### Option 3: Tests après deploy
```bash
# Dans ton CI/CD après deploy
curl https://sentinel.onrender.com/api/e2e/test
```

## Avantages

✅ **Détecte bugs frontend** que les tests serveur ratent
✅ **Screenshots automatiques** pour debug facile  
✅ **Headless** - pas besoin d'interface graphique
✅ **Rapide** - 2-3 secondes par test
✅ **Production-ready** - fonctionne sur Render/Heroku

## Ce que ça aurait détecté

Le bug `video.video_id` aurait été détecté car:
1. Test charge `/watch/121`
2. Vérifie que `video.src` existe
3. Voit que `video.src = ""` (vide)
4. ❌ **FAIL** avec message: "Video source not found - template bug"
5. Screenshot montrant player vide
6. Sentinel crée incident automatiquement

## Prochaines Étapes

1. **Ajouter plus de tests**:
   - Login flow
   - Payment flow (PPV/VIP)
   - Video upload (admin)
   - Mobile responsiveness

2. **Intégrer dans CI/CD**:
   ```yaml
   # .github/workflows/test.yml
   - name: E2E Tests
     run: |
       playwright install chromium
       python sentinel_dashboard/e2e_tester.py
   ```

3. **Monitoring continu**:
   Sentinel lance tests E2E toutes les 10 minutes sur production

## Coût

- **Playwright**: Gratuit
- **Screenshots**: ~100KB chacun
- **Temps execution**: ~8 secondes pour 4 tests
- **Impact serveur**: Minimal (1 requête par test)

---

**Résultat**: Sentinel devient **vraiment intelligent** et détecte les bugs que tu vois dans ton navigateur 🎯
