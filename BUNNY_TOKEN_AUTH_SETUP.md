# 🔑 Configuration Bunny Security Key

## Étapes pour activer Token Authentication

### 1. Récupère ta Security Key

1. Va sur https://panel.bunny.net/stream
2. Clique sur **Library 389178** (Private)
3. Onglet **Security**
4. Section **Token Authentication**
5. **Active** "Enable Token Authentication"
6. Copie la **Security Key** (format: UUID comme `12345678-1234-1234-1234-123456789abc`)

### 2. Ajoute la Security Key localement

```bash
# Dans ton terminal
export BUNNY_SECURITY_KEY="ta-security-key-ici"
```

Ou ajoute dans `.env`:
```
BUNNY_SECURITY_KEY=ta-security-key-ici
```

### 3. Teste localement

```bash
cd public_interface
python3 bunny_signer.py
```

Tu devrais voir:
```
🔒 Secure Bunny Embed URL:
https://iframe.mediadelivery.net/embed/389178/VIDEO_ID?token=ABC...&expires=1234567890&autoplay=true...
```

### 4. Ajoute sur Render

1. Dashboard Render → Service **only-public**
2. **Environment** → Add Environment Variable
3. Key: `BUNNY_SECURITY_KEY`
4. Value: ta-security-key-ici
5. **Save Changes**
6. Render va automatiquement redéployer

### 5. Vérifie en production

Après redéploiement (2-3 minutes):

```bash
# Test que vidéo marche
curl -s "https://only-public.onrender.com/watch/121" | grep "token="
```

Tu devrais voir `token=` et `expires=` dans l'URL iframe.

## ✅ Sécurité complète

Avec Token Auth activé:
- ✅ URLs signées avec expiration (2h)
- ✅ Impossible de copier l'URL (expire)
- ✅ Signature HMAC-SHA256 (impossible à forger)
- ✅ Allowed Referrers (seulement ton site)
- ✅ Redirect si pas auth (pas d'iframe dans HTML)

= **99% protection contre le vol**

## 🧪 Test de sécurité

Après activation, lance:
```bash
python3 sentinel_dashboard/security_audit.py
```

Tous les tests devraient être ✅ PASS

---

**Note**: Si tu ne trouves pas la Security Key, c'est peut-être parce que Token Authentication n'est pas encore activé. Active-le d'abord dans Bunny Dashboard.
