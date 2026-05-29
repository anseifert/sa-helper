# SA Task Hub

Greenfield task hub for a single Red Hat Solutions Architect: auto-extracted open tasks from Gmail, Calendar, and Drive; contacts from Gmail; rule-based recommendations with optional **local Ollama** wording. All data and LLM stay on your machine — no cloud AI or database.

## MVP features

| Area | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Onboarding splash until Google is connected and first sync completes; then widgets & recommendations |
| Tasks | `/tasks` | Open tasks (30d window), grouped by company, source badge + origin link |
| Contacts | `/contacts` | Gmail addresses, search/filter, company override, ignore, Ollama enrich |
| Assets | `/assets` | Subscriptions & hardware per company (from existing companies in the app) |
| Settings | `/settings` | Google OAuth, manual sync, Slack stub status |

**API:** `REST /api/v1/*` — OpenAPI at `/docs`  
**Sync:** Hourly APScheduler + `POST /api/v1/sync`  
**Webhooks:** `POST /api/v1/webhooks/register` (stub delivery logs only)

## Deploy updates to the server

After pulling new code on the server:

```bash
cd /path/to/sa-helper
docker compose up -d --build
```

Verify the new backend is running:

```bash
curl -s https://sa-hub.digitalgiants.net/api/v1/health
# Expect JSON with "app_version":"2026.05.22-recommendations-datetime" (or newer) and "auth_enabled":true

curl -s https://sa-hub.digitalgiants.net/api/v1/auth/me
# Expect {"authenticated":false,"login_configured":true,...}  — NOT {"detail":"Not Found"}
```

If `auth/me` returns **Not Found**, the backend image was not rebuilt. Run `docker compose build --no-cache backend && docker compose up -d`.

### Podman: UI or API still looks old after `podman compose up -d --build`

Usually **not** a browser problem until the server is actually running new images. Check in this order:

1. **Confirm code on the machine you build** — `git pull` in the repo directory before compose.
2. **Backend version (definitive)** — on the same host/URL you use in the browser:
   ```bash
   curl -s http://localhost:8000/api/v1/health
   # or https://sa-hub.digitalgiants.net/api/v1/health
   ```
   Compare `app_version` in JSON to what you expect. Old version → **build/deploy** (image cache, wrong host, or compose run from another checkout).
3. **Force a real rebuild** (Podman often reuses layers):
   ```bash
   podman compose build --no-cache frontend backend
   podman compose up -d --force-recreate
   ```
4. **`.env` changes** — editing `.env` does not update running containers until recreate:
   ```bash
   podman compose up -d --force-recreate
   ```
   (Rebuild is only needed for code/Dockerfile changes.)
5. **Browser** — if `app_version` is new but the UI is missing widgets, hard refresh (Cmd+Shift+R) or a private window. Frontend is static files baked into the `frontend` image; nginx now sends `no-cache` on `index.html` after you rebuild the frontend image.

6. **Wrong target** — building on your laptop but opening production (or the reverse). Build and curl health on the **same** machine/URL you browse.

## Quick start (Docker)

```bash
cd sa-task-hub
cp .env.example .env
# Edit .env: APP_PASSWORD, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, FERNET_KEY
# FERNET_KEY: backend/.venv/bin/python backend/scripts/generate_fernet_key.py

docker compose up --build -d
# Pull a local model (once):
docker compose exec ollama ollama pull llama3.2
```

- UI: http://localhost:8080  
- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

1. Set login in `.env` on the server (`APP_USERNAME=admin`, `APP_PASSWORD=…`), rebuild, then open **`/login`** and sign in with that same username/password (not your Google password).  
2. Open **Settings** → **Connect Google** (add redirect URI in Google Cloud console).  
3. **Run sync now** — populates Tasks, Contacts, Dashboard.  

## Google OAuth setup

1. Create a Google Cloud project → OAuth consent screen (internal/test).  
2. Credentials → OAuth client (Web).  
3. Authorized redirect URI: value of `GOOGLE_REDIRECT_URI` (default `http://localhost:8000/api/v1/oauth/google/callback`).  
4. Scopes: Gmail readonly, Calendar readonly, Drive readonly (configured in `.env`).
5. APIs & Services → **Library** → enable **Google Calendar API** and **Google Drive API** (required for sync; without them those connectors show `error`).

## Local development

**Backend**

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' ../.env | xargs) 2>/dev/null || true
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Tests**

```bash
cd backend && pip install pytest && pytest
```

## Layout

```
sa-task-hub/
├── backend/          # FastAPI, SQLAlchemy async, SQLite, extractors
├── frontend/         # React + Vite + TypeScript + Tailwind
├── deploy/           # Caddyfile.example
├── docker-compose.yml
├── .env.example
└── README.md
```

## Architecture notes

- **Extractors:** pluggable (`gmail`, `calendar`, `drive`, `slack` stub). Upsert idempotent on `(source, source_id)`.  
- **Recommendations:** rule-ranked scores; optional Ollama polish (degrades if Ollama down).  
- **Tokens:** Fernet-encrypted in `oauth_tokens` table.  
- **Deferred:** Slack sync, manual task CRUD, multi-user, CRM, native apps, real webhook HTTP delivery.

## Caddy (home server)

See `deploy/Caddyfile.example` — reverse-proxy `/api` and `/docs` to backend, everything else to frontend.

## Environment variables

See `.env.example`. No OpenAI/Anthropic or other cloud LLM keys are used anywhere in this repo.

**Login:** Set `APP_PASSWORD` (and optionally `APP_USERNAME`, default `admin`). Use a strong `SECRET_KEY`. For HTTPS deployments set `AUTH_COOKIE_SECURE=true`.

## Troubleshooting sync (504 Gateway Timeout)

Sync can take several minutes. Newer builds return **202 immediately** and run sync in the background; the UI polls until done. If you still see **504** from nginx:

1. Rebuild: `docker compose up -d --build`
2. If you use **host nginx** in front of Docker, increase `proxy_read_timeout` (e.g. `600s`) for `/api/`
3. If you use **Caddy**, see `deploy/Caddyfile.example` (`read_timeout 10m`)

## Troubleshooting “Could not load today's calendar” on the dashboard

**Sync health `calendar: success`** only means the **sync job** read the calendar for tasks. The **Today's meetings** widget calls the Calendar API again when you open the dashboard.

Common causes:

- **Missing timezone data in the backend container** — the widget uses `USER_TIMEZONE` (default `America/New_York`). Slim Python images need the `tzdata` package (included in recent `backend/Dockerfile`). Rebuild: `podman compose build --no-cache backend && podman compose up -d --force-recreate`.
- **Invalid `USER_TIMEZONE`** — must be an IANA name (e.g. `America/Chicago`), not `EST` or `EDT`.
- **No external meetings today** — internal-only `@redhat.com` meetings are hidden on purpose; you should see “No external meetings…” with **no** error line.
- After deploy, `curl -s …/api/v1/health` should show `app_version` `2026.05.22-calendar-today-tz` or newer.

## Troubleshooting recommendations sync (`error`)

On the dashboard **Sync health** row, expand the red text under `recommendations` — that is the real error from the last sync.

Common causes:

- **`can't compare offset-naive and offset-aware datetimes`** — calendar tasks store timezone-aware `due_at` values; older recommendation code compared them in SQL. Fixed in `app_version` `2026.05.22-recommendations-datetime` or newer. Rebuild backend: `podman compose build --no-cache backend && podman compose up -d --force-recreate`.
- **Ollama** — optional polish only; failures are skipped and should not fail sync. If you still see errors on an old image, redeploy as above.
- After a successful sync, run **Sync now** again; `recommendations` should show `success`.

```bash
curl -s http://localhost:8000/api/v1/health | grep app_version
curl -s http://localhost:8000/api/v1/sync/status
```

## Troubleshooting Google sync

- **500 on `/api/v1/oauth/google/callback`:** Ensure `.env` has `GOOGLE_REDIRECT_URI=https://your-host/api/v1/oauth/google/callback` (HTTPS, exact match with Google Console). Redeploy backend + frontend after changes. Check logs: `docker compose logs backend --tail=50` for `google_oauth_callback_failed`.
- **Drive sync fails (403):** Enable **Google Drive API** in the same Google Cloud project as your OAuth client, then reconnect Google in Settings.
- **Check which connector failed:** `GET /api/v1/sync/status`; `drive.error` has the message (all `never` means OAuth never completed).
- Set `USER_EMAIL` in `.env` to your Google address so mention filtering works.
