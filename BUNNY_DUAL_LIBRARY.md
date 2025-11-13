# 🐰 Bunny Stream - Configuration Dual Library

## Architecture

Le système ONLY utilise **2 bibliothèques Bunny Stream** pour implémenter un modèle freemium :

### 📚 Bibliothèque PRIVATE (389178)
- **Contenu** : Vidéos complètes payantes (VIP/Premium/Raw)
- **CDN** : vz-a3ab0733-842.b-cdn.net
- **Accès** : Nécessite token ONLY valide
- **Token Auth** : À activer dans Bunny Dashboard
- **Domains autorisés** : only-public.onrender.com uniquement

### 🌍 Bibliothèque PUBLIQUE (420867)
- **Contenu** : Previews/Posts gratuits (30-60s)
- **CDN** : vz-9cf89254-609.b-cdn.net
- **Accès** : Public, partage social media
- **Token Auth** : OFF
- **Domains autorisés** : * (tous)

## API Key Configuration

**Deux clés API spécifiques** (une par bibliothèque) :

**Private Library (389178)** :
```
9bf388e8-181a-4740-bf90bc96c622-3394-4591
```

**Public Library (420867)** :
```
5eb42e83-6fe9-48fb-b08c5656f422-3033-490a
```

Chaque clé donne accès uniquement à sa bibliothèque respective.

## Curator Bot API

### Synchronisation

**Sync les 2 bibliothèques** :
```bash
POST /sync/bunny
```

**Sync une seule bibliothèque** :
```bash
POST /sync/bunny?library_type=private
POST /sync/bunny?library_type=public
```

### Filtrage des vidéos

**Récupérer uniquement les previews publics** :
```bash
GET /videos?library=public
```

**Récupérer uniquement les vidéos privées** :
```bash
GET /videos?library=private
```

**Récupérer tout** :
```bash
GET /videos
```

## Base de données

Chaque vidéo dans la table `videos` a maintenant :
- `library_type` : "private" ou "public"
- `cdn_hostname` : hostname CDN approprié
- `video_url` : URL complète avec bon CDN

## Flow utilisateur

1. **Homepage (gratuite)** :
   - Affiche les vidéos avec `library=public`
   - Pas d'authentification requise
   - CTA "Watch full video" sur chaque preview

2. **Click sur CTA** :
   - Redirige vers page de login
   - Demande token ONLY

3. **Après login** :
   - Affiche les vidéos avec `library=private`
   - Filtre selon `access_level` du token (vip/premium/raw)
   - Lecteur vidéo avec vidéo complète

## Variables d'environnement (Render)

```env
# PRIVATE Library (389178)
BUNNY_PRIVATE_API_KEY=9bf388e8-181a-4740-bf90bc96c622-3394-4591
BUNNY_PRIVATE_LIBRARY_ID=389178
BUNNY_PRIVATE_CDN_HOSTNAME=vz-a3ab0733-842.b-cdn.net

# PUBLIC Library (420867)
BUNNY_PUBLIC_API_KEY=5eb42e83-6fe9-48fb-b08c5656f422-3033-490a
BUNNY_PUBLIC_LIBRARY_ID=420867
BUNNY_PUBLIC_CDN_HOSTNAME=vz-9cf89254-609.b-cdn.net
```

## Configuration Bunny Dashboard

### Bibliothèque PRIVATE (389178) ✅ DÉJÀ CONFIGURÉE
1. Security → General → **Embed view token authentication** : ✅ ON
2. Security → General → **Block direct URL access** : ✅ ON
3. Security → General → **Allowed Domains** : 
   - only-web.onrender.com
   - only-curator.onrender.com
   - only-public.onrender.com
   - *onrender.com

### Bibliothèque PUBLIQUE (420867) ✅ DÉJÀ CONFIGURÉE
1. Security → General → **Token Authentication** : OFF (normal pour contenu public)
2. Security → General → **Allowed Domains** : Aucun (partage social illimité)
3. Security → General → **Block direct URL access** : OFF (accès public)

## Marketing Strategy

**Previews publics** :
- Clips 30-60s des meilleures vidéos
- Watermark "ONLY.com" en overlay
- Partage Instagram/TikTok/Twitter
- CTA "Watch full video"

**Vidéos complètes** :
- Accessible uniquement avec token
- 3 niveaux : VIP, Premium, Raw
- Pas de watermark
- Qualité maximale
