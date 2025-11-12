# 💾 Comment Ajouter un Disk sur Render (Guide Visuel)

## 🎯 Pourquoi un Disk ?

Les **Disks** sont nécessaires pour **Gateway** et **Monetizer** car ils utilisent des bases de données SQLite (`.db`) qui doivent persister même si le service redémarre.

**Sans Disk** : La base de données est perdue à chaque redémarrage ! ❌  
**Avec Disk** : La base de données est sauvegardée en permanence ! ✅

---

## 📋 Services qui NÉCESSITENT un Disk

| Service | Disk requis ? | Pourquoi |
|---------|---------------|----------|
| **Gateway** | ✅ OUI | Stocke la queue de jobs dans `gateway.db` |
| **Monetizer** | ✅ OUI | Stocke les tokens dans `monetizer.db` |
| Narrator | ❌ Non | Pas de stockage persistant |
| Publisher | ❌ Non | Pas de stockage persistant |
| Web Interface | ❌ Non | Pas de stockage persistant |

---

## 🔧 ÉTAPES DÉTAILLÉES : Ajouter un Disk

### Scénario 1 : Pendant la création du service

Quand tu crées un service (Gateway ou Monetizer), **AVANT** de cliquer "Create Web Service" :

```
┌─────────────────────────────────────────────────────────────┐
│  Render - New Web Service                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Name: only-gateway                                          │
│  Root Directory: gateway                                     │
│  Build Command: pip install -r requirements.txt             │
│  Start Command: python gateway.py                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Environment Variables                               │     │
│  │ PORT = 5055                                        │     │
│  │ NARRATOR_URL = https://...                         │     │
│  │ DB_PATH = /data/gateway.db    👈 IMPORTANT !      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ⬇️ SCROLL EN BAS ⬇️                                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 💾 Disk                                            │     │
│  │                                                     │     │
│  │ [+ Add Disk]  👈 CLIQUE ICI !                      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  [ Create Web Service ]                                     │
└─────────────────────────────────────────────────────────────┘
```

**Clique sur "+ Add Disk"**, une popup s'ouvre :

```
┌─────────────────────────────────────────────────────────────┐
│  Add Disk                                              [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Name                                                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │ gateway-data                  👈 TAPE ÇA          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  Mount Path                                                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │ /data                         👈 TAPE ÇA          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  Size                                                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 1 GB  [▼]                     👈 LAISSE 1 GB      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  💡 Free accounts get 1 GB of storage per disk.             │
│                                                              │
│  [ Cancel ]                              [ Add Disk ]  👈   │
└─────────────────────────────────────────────────────────────┘
```

**Clique sur "Add Disk"**, puis **"Create Web Service"**.

---

### Scénario 2 : Après la création du service

Si tu as déjà créé le service **sans** ajouter le Disk, voici comment le faire après :

1. **Va dans ton service** (ex: `only-gateway`)
   ```
   Dashboard → Services → only-gateway
   ```

2. **Clique sur l'onglet "Settings"** (barre du haut)
   ```
   ┌─────────────────────────────────────────────────────────┐
   │  only-gateway                                           │
   ├─────────────────────────────────────────────────────────┤
   │  [Logs] [Settings] [Environment] [Deploy]  👈 CLIQUE   │
   └─────────────────────────────────────────────────────────┘
   ```

3. **Scroll jusqu'à la section "Disk"**
   ```
   Settings
   ├── General
   ├── Build & Deploy
   ├── Environment Variables
   ├── Health Check Path
   ⬇️ SCROLL ⬇️
   ├── 💾 Disk  👈 TU ES LÀ
   └── Danger Zone
   ```

4. **Clique sur "+ Add Disk"**
   ```
   ┌─────────────────────────────────────────────────────────┐
   │  💾 Disk                                                │
   ├─────────────────────────────────────────────────────────┤
   │  No disks configured yet.                               │
   │                                                          │
   │  [+ Add Disk]  👈 CLIQUE ICI                            │
   └─────────────────────────────────────────────────────────┘
   ```

5. **Remplis la popup** (même chose que Scénario 1)
   - **Name** : `gateway-data` (pour Gateway) ou `monetizer-data` (pour Monetizer)
   - **Mount Path** : `/data`
   - **Size** : `1 GB`

6. **Clique "Add Disk"**

7. ⚠️ **IMPORTANT** : Le service va **redémarrer automatiquement** (c'est normal)

---

## 🎯 Résultat Final

Après avoir ajouté le Disk, tu verras :

```
┌─────────────────────────────────────────────────────────────┐
│  💾 Disk                                                    │
├─────────────────────────────────────────────────────────────┤
│  ✅ gateway-data                                            │
│     Mount Path: /data                                       │
│     Size: 1 GB                                              │
│     [Remove]                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Vérification : Le Disk fonctionne ?

### Méthode 1 : Via les Logs

Après le redémarrage du service, va dans **Logs** :

```
Logs → Cherche cette ligne :

✅ "Database initialized at /data/gateway.db"
✅ "SQLite database created: /data/gateway.db"
```

Si tu vois ça → **Le Disk fonctionne !** ✅

### Méthode 2 : Via l'API

Une fois tous les services déployés, teste :

```bash
# Crée un job
curl -X POST https://only-gateway.onrender.com/event \
  -H "Content-Type: application/json" \
  -d '{"event":"test","file":"/tmp/test.mp4","timestamp":"2025-11-12T00:00:00Z"}'

# Vérifie que le job existe
curl https://only-gateway.onrender.com/jobs
```

Si tu vois le job → **Le Disk sauvegarde bien les données !** ✅

---

## 🆘 Problèmes Courants

### Erreur : "Permission denied /data"

**Solution** : Vérifie que `DB_PATH = /data/gateway.db` dans les Environment Variables (pas `/gateway.db`)

### Erreur : "No such file or directory /data"

**Solution** : Le Disk n'est pas monté. Re-vérifie qu'il est bien ajouté dans Settings → Disk.

### Service en "Failed"

**Solution** : Regarde les logs (onglet Logs). Probablement un problème de configuration des variables d'environnement.

---

## 📋 Checklist Finale

Pour **Gateway** :
- ✅ Disk ajouté : Name = `gateway-data`, Mount = `/data`, Size = `1 GB`
- ✅ Variable d'environnement : `DB_PATH = /data/gateway.db`
- ✅ Service redémarré automatiquement
- ✅ Logs affichent "Database initialized"

Pour **Monetizer** :
- ✅ Disk ajouté : Name = `monetizer-data`, Mount = `/data`, Size = `1 GB`
- ✅ Variable d'environnement : `DB_PATH = /data/monetizer.db`
- ✅ Service redémarré automatiquement
- ✅ Logs affichent "Database initialized"

---

## 💡 Astuce

Si tu veux voir ce qui est stocké dans le Disk :

1. Va dans **Shell** (onglet en haut du service)
2. Tape :
   ```bash
   ls -lh /data
   ```
3. Tu verras ton fichier `.db` !

---

**Avec ce guide, tu devrais pouvoir ajouter tes Disks sans problème !** 🚀

Besoin d'aide sur une étape précise ? Dis-moi où tu bloques !
