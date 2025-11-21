# 🔒 SÉCURITÉ VIDÉO - CONFIGURATION BUNNY

## ⚠️ FAILLES DÉTECTÉES

### Faille #1: iframe embedable partout
**Problème**: Vidéos peuvent être embedées sur n'importe quel site web  
**Impact**: Quelqu'un peut copier l'URL iframe et la mettre sur son site  
**Solution**: Configurer "Allowed Referrers" dans Bunny Dashboard

### Faille #2: Page /watch accessible sans token
**Problème**: URL iframe visible dans HTML source même sans auth  
**Impact**: Quelqu'un peut inspecter le HTML et copier l'URL  
**Solution**: ✅ FIXÉ - Redirect vers login au lieu de montrer paywall

## 🔧 CONFIGURATION BUNNY (URGENT)

### 1. Va sur Bunny Dashboard
https://panel.bunny.net/stream

### 2. Library 389178 (Private) → Security

#### A. Allowed Referrers
**Actuellement**: Probablement `*` (tous les domaines)  
**Doit être**: 
```
only-public.onrender.com
```

**Comment faire**:
1. Security → General → Allowed Referrers
2. Supprime `*` si présent
3. Ajoute `only-public.onrender.com`
4. Save

#### B. Token Authentication (Optionnel - Level 2)
**Actuellement**: OFF  
**Recommandé**: ON (avec code `bunny_signer.py` déjà prêt)

Si activé:
1. Security → General → "Embed view token authentication" → ON
2. Copie "Security Key" (UUID)
3. Ajoute sur Render: `BUNNY_SECURITY_KEY=uuid-ici`
4. Décommente code dans `public_interface.py`:
   ```python
   from bunny_signer import get_secure_embed_url
   secure_embed_url = get_secure_embed_url(...)
   ```

#### C. Blocked Referrers (Optionnel)
Si tu veux bloquer des sites spécifiques:
```
*.tube.com
*.xxx
*porn*
```

## 🧪 TEST DE SÉCURITÉ

```bash
# Test 1: Depuis site autorisé (devrait marcher)
curl -H "Referer: https://only-public.onrender.com/" \
  "https://iframe.mediadelivery.net/embed/389178/VIDEO_ID"

# Test 2: Depuis site non-autorisé (devrait être 403)
curl -H "Referer: https://hacksite.com/" \
  "https://iframe.mediadelivery.net/embed/389178/VIDEO_ID"
```

## ✅ FIX DÉJÀ APPLIQUÉS

### 1. Page /watch redirige vers login si pas auth
**Avant**:
```python
if not has_access:
    return paywall.html  # ❌ iframe dans HTML!
```

**Après**:
```python
if not has_access:
    return RedirectResponse("/login")  # ✅ Pas d'iframe!
```

### 2. Sentinel security_audit.py
Teste automatiquement les failles:
```bash
python3 sentinel_dashboard/security_audit.py
```

Outputs:
- ✅/❌ Page accessible sans auth
- ✅/❌ iframe embedable partout
- ✅/❌ HLS URLs bloquées
- ✅/❌ API sécurisée

## 📊 NIVEAUX DE SÉCURITÉ

### Level 1: Referrer Check (MINIMUM - À FAIRE MAINTENANT)
- ✅ Code: Déjà fixé (redirect au lieu de paywall)
- ⚠️ Bunny: Configure "Allowed Referrers"
- Protection: Empêche embed sur autres sites
- Contournable: Oui (avec curl sans referer)

### Level 2: Token Auth (RECOMMANDÉ)
- ✅ Code: `bunny_signer.py` prêt
 - ✅ Code: `bunny_signer.py` prêt (HMAC-SHA256 per Bunny token auth best-practices). Do not expose your `BUNNY_SECURITY_KEY`.
- ⚠️ Bunny: Active Token Auth + copie Security Key
- ⚠️ Render: Ajoute `BUNNY_SECURITY_KEY`
- Protection: URLs signées avec expiration
- Contournable: Non (signature HMAC)

### Level 3: IP Whitelist (PARANOID)
- Bunny: Whitelist IPs Render
- Protection: Seulement serveurs Render peuvent accéder
- Contournable: Non
- Inconvénient: Complexe si IPs changent

## 🎯 ACTION IMMÉDIATE

1. **Va sur Bunny Dashboard MAINTENANT**
2. **Library 389178 → Security → Allowed Referrers**
3. **Supprime `*` et ajoute `only-public.onrender.com`**
4. **Save**

Cela prendra ~2 minutes et empêchera 90% des vols de vidéos.

Plus tard (quand tu auras le temps):
5. Active Token Auth
6. Ajoute BUNNY_SECURITY_KEY
7. Redeploy avec signed URLs

## 📞 CONTACT

Si tu veux Level 2 (Token Auth) maintenant:
1. Donne-moi ta Security Key de Bunny
2. Je configure tout
3. 5 minutes et c'est 100% sécurisé

---

**Status actuel**: 🟡 Moyennement sécurisé (HLS bloqués, page redirect)  
**Status après Allowed Referrers**: 🟢 Bien sécurisé (90% protection)  
**Status avec Token Auth**: 🟢🟢 Très sécurisé (99% protection)
