# 🚨 Sentinel - Workflow des Incidents

## Quand Sentinel Détecte un Problème

### 📋 Processus Automatique (toutes les 30 secondes)

```
1. CHECK → 2. DÉTECTION → 3. DIAGNOSTIC → 4. INCIDENT → 5. AUTO-REPAIR → 6. ALERTE
```

---

## 🔴 Scénario 1: Service DOWN (Crash)

### Détection
```
[Sentinel] Check de "public" (https://only-public.onrender.com)
  ❌ Connection refused sur /
  ❌ Connection refused sur /watch/121
Status: DOWN (2/2 endpoints failed)
```

### Diagnostic Automatique
```python
{
  "issue": "Service public inaccessible",
  "cause": "Le service ne répond pas (crash ou non démarré)",
  "severity": "CRITICAL",
  "recommendation": """
    🔧 Action requise:
    1. Va sur Render Dashboard → public
    2. Vérifie les logs pour voir l'erreur
    3. Clique 'Manual Deploy' → 'Deploy latest commit'
    4. Si erreur persiste: vérifie les variables d'environnement
  """
}
```

### Ce Que Sentinel Fait
1. ✅ **Enregistre dans DB** (`incidents` table)
2. ✅ **Crée une alerte** dans le dashboard
3. ✅ **Tente auto-repair**: Ping wake-up (30s timeout)
4. ✅ **Re-check**: Si wake-up fonctionne → incident résolu auto
5. ⚠️ **Si échec**: Incident reste ouvert dans `/api/incidents`

### Dans le Dashboard
```
🚨 ALERTE ACTIVE
Service: public
Severity: CRITICAL
Issue: Service public inaccessible
Detected: 2025-11-13 17:45:23
Uptime 24h: 94.2%

📋 Recommandation:
1. Va sur Render Dashboard → public
2. Vérifie les logs pour voir l'erreur
3. Clique 'Manual Deploy' → 'Deploy latest commit'
```

---

## 🟡 Scénario 2: Service LENT (Timeout)

### Détection
```
[Sentinel] Check de "curator" (https://only-curator.onrender.com)
  ⏱️ Timeout (>5s) sur /videos
  ✅ / responded in 1200ms
Status: DEGRADED (1/2 endpoints timeout)
```

### Diagnostic Automatique
```python
{
  "issue": "Service curator en erreur",
  "cause": "Le service est trop lent ou surchargé",
  "severity": "HIGH",
  "recommendation": """
    ⚡ Action requise:
    1. Vérifie les logs de curator sur Render
    2. Cherche des boucles infinies ou requêtes lentes
    3. Considère upgrade plan (plus de RAM/CPU)
  """
}
```

### Ce Que Sentinel Fait
1. ✅ **Enregistre incident** (severity: HIGH)
2. ✅ **Tentative wake-up** (ping avec 30s timeout)
3. ✅ **Métriques**: Response time moyenne monte dans dashboard
4. ⚠️ **Pas d'auto-fix possible** (nécessite intervention manuelle)

---

## 🔒 Scénario 3: SÉCURITÉ - Token Auth Manquant

### Détection (toutes les 5 minutes)
```
[Sentinel] 🔒 Vérification sécurité vidéo...
  → Test 1: Token Auth actif?
  ❌ CRITIQUE: iframe sans token détecté!
  URL: https://iframe.mediadelivery.net/embed/389178/xxx?autoplay=true
       (pas de token= ni expires=)
```

### Diagnostic Automatique
```python
{
  "severity": "CRITICAL",
  "issue": "Iframe vidéo sans Token Auth",
  "impact": "Vidéos copiables et embeddables n'importe où",
  "fix": "Ajouter BUNNY_SECURITY_KEY=453f0507-2f2c-4155-95bd-31a2fdd3610c dans Render env vars"
}
```

### Ce Que Sentinel Fait
1. ✅ **Crée incident CRITICAL** (service: "security")
2. ✅ **Affiche dans dashboard** avec fix exact
3. ✅ **Met à jour security_score**: 33% → 100% après fix
4. ⚠️ **Pas d'auto-fix** (nécessite action manuelle sur Render)
5. ✅ **Re-check automatique** dans 5 minutes

### Dans le Dashboard
```
🚨 SÉCURITÉ CRITIQUE
Issue: Iframe vidéo sans Token Auth
Impact: Vidéos copiables et embeddables n'importe où
Score: 33% (1/3 checks PASS)

🔧 FIX URGENT:
Ajouter BUNNY_SECURITY_KEY=453f0507-2f2c-4155-95bd-31a2fdd3610c 
dans Render env vars (only-public service)
```

---

## 🟢 Scénario 4: Résolution Automatique

### Service Revient en Ligne
```
[Sentinel] Check de "public"
  ✅ / responded in 245ms
  ✅ /watch/121 responded in 312ms
Status: HEALTHY (2/2 endpoints OK)

[Sentinel] 🎉 Incident #45 résolu automatiquement
Service: public
Downtime: 2m 30s
Resolution: Service restored
```

### Ce Que Sentinel Fait
1. ✅ **Marque incident comme résolu** (DB: `resolved_at = NOW()`)
2. ✅ **Retire de la liste d'alertes** du dashboard
3. ✅ **Incrémente compteur**: `auto_fixes++`
4. ✅ **Calcule uptime**: Prend en compte le downtime

---

## 📊 API Endpoints pour Consulter

### Voir Incidents Actifs
```bash
curl https://only-sentinel.onrender.com/api/incidents?open_only=true
```
**Résultat:**
```json
{
  "incidents": [
    {
      "id": 127,
      "service": "security",
      "severity": "CRITICAL",
      "issue": "Iframe vidéo sans Token Auth",
      "detected_at": "2025-11-13T17:45:23",
      "resolved_at": null,
      "recommendation": "Ajouter BUNNY_SECURITY_KEY=... dans Render"
    }
  ]
}
```

### Vérifier Sécurité
```bash
curl https://only-sentinel.onrender.com/api/security/status
```
**Résultat:**
```json
{
  "secure": true,
  "security_score": 100,
  "checks": [
    {"name": "Token Auth présent", "status": "PASS"},
    {"name": "HLS direct access blocked", "status": "PASS"},
    {"name": "API metadata protection", "status": "PASS"}
  ],
  "vulnerabilities": []
}
```

### État Système Complet
```bash
curl https://only-sentinel.onrender.com/api/status
```
**Résultat:**
```json
{
  "services": {
    "public": {
      "status": "healthy",
      "response_time_ms": 245,
      "uptime_24h": 99.2
    },
    "curator": {...}
  },
  "alerts": [],
  "metrics": {
    "total_checks": 15823,
    "total_incidents": 12,
    "auto_fixes": 8
  },
  "security": {
    "secure": true,
    "security_score": 100
  }
}
```

---

## 🎯 Ce Que Sentinel NE Fait PAS

### ❌ Limitations

**1. Pas de Restart Automatique**
- Render Free n'a pas d'API pour restart
- Solution: Sentinel tente wake-up, sinon tu dois redeploy manuellement

**2. Pas d'Envoi d'Emails/SMS**
- Nécessiterait SendGrid/Twilio (payant)
- Solution: Consulte dashboard ou API `/incidents`

**3. Pas de Fix de Bugs**
- Sentinel ne peut pas corriger ton code Python
- Solution: Il te dit exactement quoi faire (logs, fix, deploy)

**4. Pas de Scaling**
- Free tier = 1 instance fixe
- Solution: Upgrade vers plan payant si nécessaire

---

## 💡 Best Practices

### 1. Consulte le Dashboard Régulièrement
```
https://only-sentinel.onrender.com/
```
Refresh automatique toutes les 30 secondes

### 2. Check les Incidents Ouverts
```bash
curl https://only-sentinel.onrender.com/api/incidents?open_only=true
```

### 3. Surveille le Score de Sécurité
```bash
curl https://only-sentinel.onrender.com/api/security/status
```
**Target: 100%** (tous les checks PASS)

### 4. Active les Notifications (futur)
Dans `.env`:
```bash
ALERT_EMAIL=ton@email.com
ALERT_TELEGRAM_CHAT_ID=123456789
```
(Nécessite setup SendGrid/Telegram Bot)

---

## 🔍 Résumé Rapide

| Problème | Détection | Auto-Fix | Action Requise |
|----------|-----------|----------|----------------|
| Service DOWN | 2 échecs consécutifs | Wake-up ping (30s) | Redeploy si échec |
| Service LENT | Timeout >5s | Wake-up ping | Check logs + upgrade plan |
| Erreur 500 | HTTP 500 | ❌ Non | Fix bug dans code |
| Token Auth manquant | Pas de `token=` dans URL | ❌ Non | Ajouter BUNNY_SECURITY_KEY |
| HLS accessible | HTTP 200 (devrait être 403) | ❌ Non | Activer CDN Token Auth |
| API leak VIP | Vidéos VIP dans API publique | ❌ Non | Filtrer access_level |

**Sentinel = 🛡️ Gardien 24/7 de ton système!**
