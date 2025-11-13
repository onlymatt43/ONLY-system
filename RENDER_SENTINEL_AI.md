# Sentinel AI - Variables d'environnement Render

## Variables EXISTANTES (déjà configurées)
```bash
PORT=10000
GATEWAY_URL=https://only-gateway.onrender.com
CURATOR_URL=https://only-curator.onrender.com
NARRATOR_URL=https://only-narrator.onrender.com
BUILDER_URL=https://only-builder.onrender.com
PUBLISHER_URL=https://only-publisher.onrender.com
REFRESH_SEC=5
```

## Variables NOUVELLES à ajouter

**⚠️ IMPORTANT: Ajouter ces 2 nouvelles variables sur Render:**

```bash
MONETIZER_URL=https://only-monetizer.onrender.com
PUBLIC_URL=https://only-public.onrender.com
```

## Variable optionnelle

```bash
MONITOR_INTERVAL_SEC=30
```
*Si non définie, Sentinel AI utilise 30 secondes par défaut pour le monitoring continu.*

---

## Fonctionnalités Sentinel AI Tier 2

✅ **HealthChecker**: Score santé 0-100, détection anomalies
✅ **MetricsCollector**: Historique 30 jours (SQLite), P95/P99 latence
✅ **AutoHealer**: Wake-up automatique services endormis (502/504)
✅ **ChatInterface**: Commandes NLP (status, metrics, alerts, restart)
✅ **Alertes**: 3 niveaux (INFO, WARNING, CRITICAL)

## Nouvelles routes API

- `GET /chat` - Interface chat HTML
- `GET /api/system/health` - Score santé système + métriques agrégées
- `GET /api/metrics/{service}?hours=24` - Statistiques détaillées service
- `GET /api/alerts` - Liste alertes non résolues
- `POST /api/chat` - Dialogue avec Sentinel AI
- `POST /api/heal/{service}` - Forcer healing manuel

## Commandes Chat

**Exemples:**
- `status` → Santé globale système
- `status gateway` → Santé service spécifique
- `metrics curator` → Stats 1h + 24h
- `show alerts` → Alertes actives
- `restart narrator` → Wake-up service
- `help` → Liste commandes

## Architecture extensible Tier 3-4

Le code est prêt pour:
- **Tier 3**: Render API (restart automatique via API), rollback deploys
- **Tier 4**: Prédictions ML, scaling automatique, optimisations proactives

## Test après déploiement

```bash
# Health score
curl https://only-sentinel.onrender.com/api/system/health

# Chat test
curl -X POST https://only-sentinel.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"status"}'

# Metrics
curl https://only-sentinel.onrender.com/api/metrics/Gateway?hours=1
```
