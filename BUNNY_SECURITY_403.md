# 🔒 Bunny Stream - Sécurité Vidéo

## Problème: Vidéos en 403 Forbidden

Les vidéos retournent 403 parce que **Token Authentication** est activé sur la library private (389178) mais l'iframe n'inclut pas de token signé.

## Solutions

### Option 1: Désactiver Token Auth (RAPIDE - Recommandé pour MVP)

1. Va sur https://panel.bunny.net/stream
2. Clique sur **Library 389178** (Private)
3. Onglet **Security**
4. Section **General**
5. **Désactive** "Embed view token authentication"
6. Save

✅ **Avantages**:
- Fonctionne immédiatement
- Pas de code additionnel
- Simple à tester

⚠️ **Inconvénients**:
- Moins sécurisé (URL direct accessible)
- Pas de contrôle fin des permissions

### Option 2: Signed URLs avec Security Key (PRODUCTION)

Code déjà implémenté dans:
- `public_interface/bunny_signer.py` - Génère tokens signés
- `public_interface/public_interface.py` - Intégré dans route `/watch/{id}`
- `templates/watch.html` - Utilise `{{ secure_embed_url }}`

**Setup requis**:

1. **Récupère Security Key**:
   - Dashboard Bunny → Library 389178 → Security
   - Copie "Security Key" (format UUID)

2. **Ajoute variable d'environnement**:
   ```bash
   export BUNNY_SECURITY_KEY="ton-uuid-ici"
   ```

3. **Sur Render**:
   - Dashboard → only-public service
   - Environment → Add variable
   - `BUNNY_SECURITY_KEY` = `ton-uuid-ici`

4. **Test local**:
   ```bash
   cd public_interface
   python3 bunny_signer.py
   ```

✅ **Avantages**:
- Très sécurisé (tokens signés avec expiration)
- URLs temporaires (2h par défaut)
- Contrôle granulaire (par vidéo, par user)

⚠️ **Inconvénients**:
- Nécessite Security Key
- URLs expirent (besoin refresh)

## Configuration Actuelle

### Library PRIVATE (389178)
- **Token Auth**: ✅ ON (c'est pourquoi 403)
- **Allowed Domains**: only-public.onrender.com
- **Direct URL Block**: ✅ ON

### Library PUBLIC (420867)
- **Token Auth**: ❌ OFF (previews gratuits)
- **Allowed Domains**: * (tous)
- **Direct URL Block**: ❌ OFF

## Recommandation

Pour lancer rapidement:
1. **Désactive Token Auth** sur library 389178 (Option 1)
2. Teste que vidéos marchent
3. Plus tard, active Token Auth + ajoute Security Key (Option 2)

OU si tu veux 100% sécurisé maintenant:
1. Récupère Security Key de Bunny Dashboard
2. Ajoute `BUNNY_SECURITY_KEY` dans variables Render
3. Redeploy

## Code Bunny Signer

Le signer génère des URLs comme:
```
https://iframe.mediadelivery.net/embed/389178/VIDEO_ID?token=ABC123&expires=1234567890
```

Le token est:
```python
# HMAC-SHA256 de: library_id/video_id/expiration
signature = hmac.new(BUNNY_SECURITY_KEY, data, sha256)
token = base64url(signature)
```

Bunny vérifie:
1. Signature valide avec sa Security Key
2. Timestamp pas expiré
3. Domain dans Allowed Domains

## Debug 403

Si tu vois toujours 403:

1. **Check Allowed Domains**:
   - Doit inclure `only-public.onrender.com`
   - Ou `*.onrender.com`
   - Ou `*` (tous - pas recommandé)

2. **Check Token Auth**:
   - Si ON → besoin token signé
   - Si OFF → devrait marcher

3. **Check Direct URL Access**:
   - Si ON → URLs HLS bloquées
   - Mais iframe embed devrait marcher

4. **Test l'embed URL directement**:
   ```bash
   curl -I "https://iframe.mediadelivery.net/embed/389178/VIDEO_ID"
   ```
   - 200 = OK
   - 403 = Problème auth/domain
   - 404 = Vidéo existe pas

## Sentinel E2E Test

Le test E2E vérifie maintenant:
```python
# Vérifie que l'iframe charge
page.wait_for_selector(".om-video-card iframe")

# Vérifie URL contient library ID
assert "389178" in iframe_src

# Vérifie token si Token Auth activé
if token_auth_enabled:
    assert "token=" in iframe_src
    assert "expires=" in iframe_src
```

---

**Action immédiate**: Va sur Bunny Dashboard et désactive Token Auth pour que ça marche maintenant. On activera la sécurité après.
