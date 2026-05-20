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

## Quick start (Docker)

```bash
cd sa-task-hub
cp .env.example .env
# Edit .env: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, FERNET_KEY
# FERNET_KEY: backend/.venv/bin/python backend/scripts/generate_fernet_key.py

docker compose up --build -d
# Pull a local model (once):
docker compose exec ollama ollama pull llama3.2
```

- UI: http://localhost:8080  
- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

1. Open **Settings** → **Connect Google** (add redirect URI in Google Cloud console).  
2. **Run sync now** — populates Tasks, Contacts, Dashboard.  

## Google OAuth setup

1. Create a Google Cloud project → OAuth consent screen (internal/test).  
2. Credentials → OAuth client (Web).  
3. Authorized redirect URI: value of `GOOGLE_REDIRECT_URI` (default `http://localhost:8000/api/v1/oauth/google/callback`).  
4. Scopes: Gmail readonly, Calendar readonly, Drive readonly (configured in `.env`).

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
