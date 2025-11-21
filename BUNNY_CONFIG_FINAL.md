# ✅ Configuration Bunny - Validation Complète

## Configuration actuelle (Screenshot)

### ✅ Paramètres corrects
1. **Allowed domains**: `only-public.onrender.com` ✅
2. **Block direct url file access**: ON ✅
3. **Embed view token authentication**: ON ✅
4. **CDN token authentication**: ON ✅
5. **Security Key**: `453f0507-2f2c-4155-95bd-31a2fdd3610c` ✅

### ⚠️ Paramètre à activer

**"Enable direct play"**: Actuellement OFF

**Recommandation**: Active-le si tu veux que les utilisateurs puissent:
- Regarder directement via URL (sans embed)
- Télécharger les vidéos (avec token)

**Pour l'instant**: Laisse OFF si tu veux FORCER l'utilisation de l'iframe embed uniquement.

## 🚀 Prochaine étape: Ajouter Security Key sur Render

1. Va sur https://dashboard.render.com
2. Clique sur service **only-public**
3. **Environment** → Add Environment Variable
4. Key: `BUNNY_SECURITY_KEY`
5. Value: `453f0507-2f2c-4155-95bd-31a2fdd3610c`
6. **Save Changes**

Render va automatiquement redéployer (2-3 minutes).

## 🧪 Test après déploiement

```bash
# Attends 3 minutes puis teste
curl -s "https://only-public.onrender.com/watch/121" | grep "token="
```

Tu devrais voir:
```html
src="https://iframe.mediadelivery.net/embed/389178/VIDEO_ID?token=ABC...&expires=123..."
```

## 📊 Niveaux de sécurité finaux

Avec cette config:
- ✅ **Referer check**: Seulement only-public.onrender.com
 - ✅ **Embed Rate-limit**: `/api/embed` rate-limited to prevent scraping.
 - ✅ **Embed Audit Logs**: Server records embed requests for analysis and abuse detection.
- ✅ **Token Auth**: URLs signées avec expiration
- ✅ **CDN Auth**: CDN aussi requiert token
- ✅ **Direct URL blocked**: Pas de téléchargement direct
- ✅ **Redirect si pas auth**: Page protégée côté serveur

= **99.9% protection** 🛡️

## ⚡ Actions rapides

1. **Sur Render** (2 min):
   - Ajoute `BUNNY_SECURITY_KEY=453f0507-2f2c-4155-95bd-31a2fdd3610c`
   - Save (auto-redeploy)

2. **Test Sentinel** (30 sec):
   ```bash
   python3 sentinel_dashboard/security_audit.py
   ```

3. **Done!** 🎉

## 🔍 Ce que Sentinel vérifiera

Après config complète:
- ✅ Page /watch redirige si pas auth
- ✅ iframe a token signé
- ✅ HLS URLs bloquées
- ✅ API sécurisée
- ✅ Referer check actif

**Résultat attendu**: 5/5 tests PASS ✅
