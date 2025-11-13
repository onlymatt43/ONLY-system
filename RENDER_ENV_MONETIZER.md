# 🔐 Variables d'environnement Render - only-monetizer

**À copier dans Render Dashboard → only-monetizer → Environment**

```env
PORT=10000

TURSO_DATABASE_URL=libsql://only-tokens-onlymatt43.aws-us-east-2.turso.io

TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjMwMDA4ODEsImlkIjoiMDcwYzdkOGEtZGUwZC00OGExLWI5NmMtNjlkN2U5MDkxODYzIiwicmlkIjoiOGQyNWI5M2QtOTJhMy00MzgxLWJhN2ItZjM3MGFhYmUxZDc2In0.y8jY7sYrNg2q88su0IK8RcVo0pqDgGjqEfneuMEptWfylVCgAqJv-X1e9L3hrzpz_IYTmjNbs4uJGiJdE7CWAg

SECRET_KEY=0mO2mPJISGYEf00nnvwvGfdT2D9LilVYcz29cdpIDbeF2odFK5z-JAXsNx1bYMjPYwUAhWDQ067Mlo-9zi038g

CODE_PREFIX=ONLY
```

---

## 📋 Checklist

1. ✅ Copier les 5 variables ci-dessus
2. ⏳ Aller sur https://dashboard.render.com
3. ⏳ Service **only-monetizer** → Onglet **Environment**
4. ⏳ Coller/éditer chaque variable
5. ⏳ Save changes
6. ⏳ Cliquer **"Manual Deploy"** (bouton en haut à droite)
7. ⏳ Attendre 2-3 minutes (build + déploiement)
8. ⏳ Tester avec:
   ```bash
   curl -X POST https://only-monetizer.onrender.com/mint \
     -H "Content-Type: application/json" \
     -d '{"title":"VIP Test Turso","access_level":"vip","duration_days":365}'
   ```

---

## ⚠️ Explications

- **PORT=10000**: Imposé par Render (pas 5060)
- **TURSO_DATABASE_URL**: Protocol `libsql://` (pas `https://`)
- **TURSO_AUTH_TOKEN**: JWT depuis Turso CLI
- **SECRET_KEY**: Nouveau généré cryptographiquement (86 caractères)
- **CODE_PREFIX=ONLY**: Correct (pas OM43)

---

**Après déploiement, les tokens auront format: `ONLY-XXXX-XXXX`**
