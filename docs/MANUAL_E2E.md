# Manual end-to-end test guide

Do not mark a step passed unless you observed it.

1. Copy `backend/.env.example` → `backend/.env` and `frontend/.env.example` → `frontend/.env`. Fill real keys (never commit them).
2. Run `supabase/schema.sql` then `supabase/seed.sql` in the Supabase SQL Editor.
3. Create a counsellor Auth user whose email is listed in `COUNSELLOR_EMAILS`. Confirm the email if required.
4. Start backend (`uvicorn main:app --reload --port 8000`) and frontend (`npm run dev`). Restart both after any `.env` change.
5. `GET http://localhost:8000/health` shows `openai_configured: true`, `supabase_configured: true`, and `missing_settings: []`.
6. Submit `/intake` with storage consent. Without consent, validation blocks submit.
7. After submit, a decision brief opens at `/report/:id` with source URLs from the knowledge base (not invented).
8. In Supabase Table Editor, confirm matching `leads` and `decision_briefs` rows.
9. Sign in at `/login` with the counsellor Auth user. Wrong password and unconfirmed email should show specific errors. An email not on `COUNSELLOR_EMAILS` can sign in to Supabase but must receive 403 from `/api/leads`.
10. Open `/counsellor`, find the lead, update follow-up status, refresh, and confirm it persists (`lead_events` row).
11. Open `/dashboard` and confirm counts include the same lead (adjust date range if needed). Seeded rows are marked demo/synthetic.
12. Repeat intake with language Hindi; brief body is Hindi, URLs remain unchanged.
13. If AI fails after intake is saved, retry generates the brief for the same lead ID (no duplicate lead).
