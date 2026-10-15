# NIAT DecisionBridge AI

Independent prototype for the **NxtWave Jr. Growth Manager — Growth Hack Challenge (Track B)**.  
Helps prospective students and parents get **sourced AI decision briefs**, gives counsellors CRM context, and measures experiment metrics from shared Supabase data.

> **Not an official NIAT product.** No implied partnership or affiliation.

## Architecture

- **Frontend:** React + TypeScript + Vite + Tailwind + React Router + React Hook Form + Zod + Recharts  
- **Backend:** FastAPI + Pydantic + OpenAI SDK + Supabase (service role, server-side only)  
- **Database:** Supabase PostgreSQL (`supabase/schema.sql`, `supabase/seed.sql`)

Workflow: **Intake → validate consent → retrieve verified docs → OpenAI brief → persist lead + brief → counsellor CRM → analytics dashboard**

## Repository layout

```
backend/           FastAPI API (main.py, app/, tests/)
frontend/          Vite React app
supabase/          schema.sql + seed.sql
render.yaml        Render backend template
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Supabase project
- OpenAI API key

---

## 1. Supabase setup

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** and run, in order (safe to re-run):
   - `supabase/schema.sql`
   - `supabase/seed.sql`
3. Copy from **Project Settings → API**:
   - Project URL → `SUPABASE_URL` **and** `VITE_SUPABASE_URL`
   - `anon` / publishable key → `VITE_SUPABASE_ANON_KEY` (frontend only)
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (backend only, never in frontend)
4. Optional: **JWT Secret** → `SUPABASE_JWT_SECRET`. If omitted, the backend verifies counsellor sessions through Supabase Auth.
5. **Authentication → Providers → Email:** for local testing you may disable **Confirm email**.
6. **Authentication → Users → Add user:** create a counsellor with email/password. Confirm the email if confirmation is enabled.
7. Put that exact email in backend `COUNSELLOR_EMAILS`.

---

## 2. Backend (Windows PowerShell)

```powershell
cd C:\Users\ankit\niat-decisionbridge-ai\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with your keys
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Backend (macOS / Linux)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Backend environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (real AI) | OpenAI API key |
| `OPENAI_MODEL` | No | Default `gpt-4o-mini` |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Service role (server only) |
| `SUPABASE_JWT_SECRET` | Yes | Verifies counsellor JWTs |
| `COUNSELLOR_EMAILS` | Yes | Comma-separated allowed emails |
| `CORS_ORIGINS` | Yes | Frontend origin(s), comma-separated |
| `EXPERIMENT_TREATMENT_RATIO` | No | Default `0.5` for A/B assignment |

---

## 3. Frontend

```powershell
cd C:\Users\ankit\niat-decisionbridge-ai\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Edit `frontend/.env` (copy from `.env.example` if the file does not exist):

```
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

Vite only reads `VITE_*` variables at **startup**. After editing `.env`, stop and restart `npm run dev`.

Open `http://localhost:5173`.

If counsellor sign-in still says auth is not configured, the frontend env file is missing or still contains placeholders.

---

## 4. Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

```bash
cd frontend && npm run build
```

---

## 5. Manual end-to-end checklist

1. **Health:** `GET http://localhost:8000/health` → `openai_configured` and `supabase_configured` true after `.env` setup.
2. **Intake:** `/intake` → complete all steps with **storage consent** checked; optional follow-up + email.
3. **Real AI:** Submit → backend calls OpenAI → redirect to `/report/:id` with verified facts + source URLs.
4. **Persistence:** Row appears in Supabase `leads` and `decision_briefs`.
5. **Counsellor:** Sign in at `/login` → `/counsellor` → search/filter lead → open brief link.
6. **Status update:** Mark follow-up status → check `lead_events` and updated lead row.
7. **Dashboard:** `/dashboard` shows funnel, time series, rates, control vs treatment (includes demo seed note if applicable).
8. **Hindi:** Intake language **Hindi** → brief content in Devanagari (URLs stay Latin).

If `OPENAI_API_KEY` is missing, brief generation returns **503** with a clear error (no fabricated AI text).

---

## 6. Deployment

### Frontend — Vercel

1. Import repo, set **Root Directory** to `frontend`.
2. Environment variables:
   - `VITE_API_BASE_URL` = your Render API URL (e.g. `https://your-api.onrender.com`)
   - `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
3. Deploy. SPA routing uses `frontend/vercel.json`.

### Backend — Render

1. Create **Web Service**, connect repo.
2. Use `render.yaml` or manually:
   - **Build:** `pip install -r backend/requirements.txt`
   - **Start:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Set all backend env vars; set `CORS_ORIGINS` to your Vercel URL (no trailing slash).

### Post-deploy verification

- `GET https://YOUR_API/health`
- Intake from production frontend
- Counsellor login + dashboard load

No live public URL is claimed until you deploy and verify.

---

## API overview

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | Public |
| POST | `/api/intake` | Public |
| POST | `/api/decision-brief` | Public |
| GET | `/api/decision-brief/{id}` | Public |
| GET | `/api/leads` | Counsellor JWT |
| GET | `/api/leads/{id}` | Counsellor JWT |
| PATCH | `/api/leads/{id}/follow-up` | Counsellor JWT |
| PATCH | `/api/leads/{id}/application` | Counsellor JWT |
| GET | `/api/dashboard/analytics` | Counsellor JWT |
| GET | `/api/knowledge/search` | Counsellor JWT |

OpenAPI docs: `http://localhost:8000/docs`

---

## Security notes

- Service role and OpenAI keys stay on the backend only.
- RLS enabled; public clients should not write leads directly.
- Counsellor authorization enforced on protected API routes via JWT + email allowlist.
- Do not commit `.env` files.

---

## Final manual configuration checklist

- [ ] Supabase schema + seed executed  
- [ ] Counsellor Auth user created  
- [ ] `COUNSELLOR_EMAILS` matches counsellor user  
- [ ] Backend `.env` complete  
- [ ] Frontend `.env` complete  
- [ ] Local E2E checklist passed  
- [ ] Render + Vercel env vars and CORS aligned  
