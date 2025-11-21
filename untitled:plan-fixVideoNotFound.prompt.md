# Plan: Fix "video not found" on Public Interface (watch route)

## Goal
Fix the "video not found" issue on the public interface watch page by ensuring the watch route uses the correct Bunny `library_type`, generates a signed embed URL for private videos, and passes a consistent video object to the watch template.

---

## Files to modify
- `public_interface/public_interface.py`
  - Add imports and env vars
  - Determine `library_type` and pick the correct library ID
  - Call `get_secure_embed_url` for private videos and pass `secure_embed_url` to the template
  - Normalize `video` keys for template (e.g., `video_id` alias for `bunny_video_id`)

- `public_interface/templates/watch.html`
  - Use `src="{{ secure_embed_url or iframe_url }}"` in iframe
  - Add friendly fallback message (login / restricted content) when neither URL is present

- `curator_bot/curator_bot.py` (optional but recommended)
  - Return a `video_id` alias in the API `GET /videos` responses
  - Ensure `library_type` is present in the DB and API response

- `public_interface/test_bunny.py`
  - Add or adapt test to ensure `get_secure_embed_url` generates URL for private library with `BUNNY_SECURITY_KEY` set
  - Add integration test that checks `/watch/{id}` includes `token=` for private videos

- Documentation files
  - `RENDER_CHECKLIST.md` / `BUNNY_TOKEN_AUTH_SETUP.md`: ensure `BUNNY_SECURITY_KEY` is listed for `only-public` service

---

## Root Cause (short)
1. `public_interface` was not consistently respecting `library_type` (private vs public) when deciding which CDN/library to use.
2. The `secure_embed_url` is not generated or is missing, so videos in private library (Token Auth ON) result in 403 or appear missing in the public interface.
3. Template property mismatch (`bunny_video_id` vs `video_id`) caused the watch page to fail rendering.

---

## Detailed Implementation Steps
1. Add imports and env var reads at top of `public_interface/public_interface.py`:
   - `from public_interface.bunny_signer import get_secure_embed_url`
   - `BUNNY_PRIVATE_LIBRARY_ID = os.getenv('BUNNY_PRIVATE_LIBRARY_ID')`
   - `BUNNY_PUBLIC_LIBRARY_ID = os.getenv('BUNNY_PUBLIC_LIBRARY_ID')`
   - `BUNNY_SECURITY_KEY = os.getenv('BUNNY_SECURITY_KEY')`

2. In `@app.get("/watch/{video_id}")` route:
   - After fetching `video` from DB (Curator), determine `library_type = video.get('library_type', 'private')`.
   - Set `library_id = (BUNNY_PUBLIC_LIBRARY_ID if library_type == 'public' else BUNNY_PRIVATE_LIBRARY_ID)`.
   - Generate `secure_embed_url = None`.
   - If `library_type == 'private'` and `BUNNY_SECURITY_KEY` is set: call
     - `secure_embed_url = get_secure_embed_url(library_id=int(library_id), video_id=bunny_video_id, security_key=BUNNY_SECURITY_KEY, autoplay=True)`.
   - If not private: build the `iframe_url` using `video['video_url']` or `cdn_hostname` and `bunny_video_id`.
   - Normalize `video` object fields for template:
     - `video['video_id'] = video.get('bunny_video_id')`
     - `video['cdn_hostname'] = video.get('cdn_hostname') or parsed_from_video_url`
   - Add debug log entries to print `library_type`, `library_id`, and `secure_embed_url` (masked if needed).

3. In `public_interface/templates/watch.html`:
   - Change the iframe source attribute to: `src="{{ secure_embed_url or iframe_url }}"`
   - If both are empty, show a message like: "Contenu restreint — connectez-vous ou abonnez-vous" and show login/subscribe CTA.

4. Update `curator_bot` API
   - In `curator_bot/curator_bot.py`, return `video_id` alias and include `library_type` in the JSON payload: `{'id': id, 'video_id': bunny_video_id, 'library_type': library_type, ...}`.

5. Add tests
   - `public_interface/test_bunny.py` should:
     - Validate `get_secure_embed_url` returns a non-empty string when `BUNNY_SECURITY_KEY` is set
     - For the `watch` route, fetch the page and assert the HTML contains `token=` for private videos; else assert raw `iframe` with public hostname.

6. Document on Render
   - Ensure `only-public` has `BUNNY_SECURITY_KEY` set in Render's env variables.
   - Add note in `RENDER_CHECKLIST.md` and `BUNNY_TOKEN_AUTH_SETUP.md` to include the security key.

---

## Local Testing Commands
- Start curator and public interface:
```zsh
cd curator_bot
python3 curator_bot.py &

cd public_interface
python3 public_interface.py &
```

- Trigger sync (if needed):
```zsh
curl -X POST http://localhost:5061/sync/bunny
```

- List videos (observe `id` and `library_type`):
```zsh
curl http://localhost:5061/videos | jq '.[0]'
```

- Open watch page in browser:
```
http://localhost:5062/watch/123  # replace 123 with curator id
```

- Quick check for signed embed URL:
```zsh
python3 - <<PY
from public_interface.bunny_signer import get_secure_embed_url
print(get_secure_embed_url(library_id=389178, video_id='VIDEO_UUID'))
PY
curl -I -H "Referer: http://localhost:5062" "$(python3 - <<PY
from public_interface.bunny_signer import get_secure_embed_url
print(get_secure_embed_url(library_id=389178, video_id='VIDEO_UUID'))
PY
)"
```

---

## Notes / Security
- If `BUNNY_SECURITY_KEY` is missing when `library_type == 'private'`, the signed URL generation will fail — add a descriptive error or fallback for developers.
- Optionally add an endpoint to generate signed tokens server-side after verifying user access (stronger security model — avoids sending the signing key to the client).

---

## Next Steps (if you want me to implement now)
- I can prepare a patch for `public_interface/public_interface.py` and `public_interface/templates/watch.html`, plus a change in `curator_bot/curator_bot.py` to add the `video_id` alias.
- I can create a small unit test `public_interface/test_bunny.py`.
- Validate the changes locally and provide logs / outputs for verification.

Please confirm if you want me to implement the patch now (I will then add the patch files to the workspace).