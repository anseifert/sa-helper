# SA Task Hub

Greenfield task hub for a single Red Hat Solutions Architect: auto-extracted open tasks from Gmail, Calendar, and Drive; contacts from Gmail; rule-based recommendations with optional **local Ollama** wording. All data and LLM stay on your machine — no cloud AI or database.

## MVP features

| Area | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Top recommendations, focus-for-today (≤5), widgets (aging, companies, sync health) |
| Tasks | `/tasks` | Open tasks (30d window), grouped by company, source badge + origin link |
| Contacts | `/contacts` | Gmail addresses, search/filter, company override, Ollama enrich |
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
# Expect JSON with "app_version":"2026.05.21-auth-login" and "auth_enabled":true

curl -s https://sa-hub.digitalgiants.net/api/v1/auth/me
# Expect {"authenticated":false,"login_configured":true,...}  — NOT {"detail":"Not Found"}
```

If `auth/me` returns **Not Found**, the backend image was not rebuilt. Run `docker compose build --no-cache backend && docker compose up -d`.

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

## Troubleshooting Google sync

- **500 on `/api/v1/oauth/google/callback`:** Ensure `.env` has `GOOGLE_REDIRECT_URI=https://your-host/api/v1/oauth/google/callback` (HTTPS, exact match with Google Console). Redeploy backend + frontend after changes. Check logs: `docker compose logs backend --tail=50` for `google_oauth_callback_failed`.
- **Drive sync fails (403):** Enable **Google Drive API** in the same Google Cloud project as your OAuth client, then reconnect Google in Settings.
- **Check which connector failed:** `GET /api/v1/sync/status`; `drive.error` has the message (all `never` means OAuth never completed).
- Set `USER_EMAIL` in `.env` to your Google address so mention filtering works.
