# MEMORY.md — Agent Context (token-optimized)

> Read THIS file first, before opening any source file. It is the single source of truth
> for project state. Goal: **minimum tokens**. Trust the ledger below instead of
> re-reading files. Only open a file whose status is `TODO` or the one you are editing.

## Token-saving rules (follow strictly)
1. **Do NOT read a file marked `DONE`** unless you are about to modify it. Its contract is summarized here.
2. **Never re-generate or re-read frontend files** (`templates/`, `static/`) once `DONE`.
   They rarely change; assume they match the contract below.
3. **Do NOT read `venv/`, `.git/`, or `PLAN.md`** during coding. PLAN.md is the spec —
   its essentials are mirrored here; read it only if this file is insufficient.
4. Prefer **grep/glob for a symbol** over reading a whole file. Read only the needed range.
5. When you finish a file, **flip its status here to `DONE` + one-line contract**. Keep contracts ≤1 line.
6. Keep this file short. Summaries, not code. If a section grows past a few lines, compress it.

## Project one-liner
FastAPI + LangGraph "AI Trip Planner". Chat extracts trip intent → LangGraph pipeline
(flights/hotels/activities → Groq itinerary JSON) → dashboard treasure-map + HTML email.

## Fixed facts (never re-derive)
- LLM: Groq `openai/gpt-oss-120b` via `langchain-groq.ChatGroq`. Env: `GROQ_API_KEY`, `GROQ_MODEL`.
- Flights: AviationStack, env `AVIATIONSTACK_STACK_API_KEY` (note the double STACK).
- Hotels+activities: Tavily, env `TAVILY_API_KEY`.
- DB: `DATABASE_URL` (postgres@localhost:5433/postgres). SQLAlchemy, `Base.metadata.create_all`.
- Email: Gmail SMTP `smtp.gmail.com:587` STARTTLS. Env `GMAIL_EMAIL`, `GMAIL_SMTP_PASSWORD`.
- Auth: bcrypt + JWT in httpOnly cookie. Env `SECRET_KEY` (add if missing).
- Itinerary JSON schema is FIXED — see PLAN.md §5; do not invent new fields.

## File ledger (status + contract)
Status: `TODO` = not built · `DONE` = built, don't re-read · `WIP` = in progress

| File | Status | Contract (what it exposes) |
|---|---|---|
| `.env` | DONE | secrets; may need `SECRET_KEY`, `GROQ_MODEL` added |
| `requirements.txt` | TODO | pinned deps (see PLAN.md) |
| `app/config.py` | TODO | `settings` (pydantic-settings) — all env vars |
| `app/database.py` | TODO | `engine`, `SessionLocal`, `Base`, `get_db()` |
| `app/models.py` | TODO | `User`, `TripPlan`, `ChatSession` |
| `app/auth.py` | TODO | `hash_pw`, `verify_pw`, `make_jwt`, `get_current_user` |
| `app/agents/state.py` | TODO | `TripState` TypedDict |
| `app/agents/tools.py` | TODO | `flight_search`, `hotel_search`, `activity_search` (@tool) |
| `app/agents/llm.py` | TODO | `get_llm()` -> ChatGroq |
| `app/agents/prompts.py` | TODO | system prompts, JSON-schema instruction |
| `app/agents/nodes.py` | TODO | node fns: extract_intent, planner, persist, send_email |
| `app/agents/graph.py` | TODO | `build_graph()` -> compiled StateGraph |
| `app/routers/auth_routes.py` | TODO | /signup /login /logout |
| `app/routers/chat_routes.py` | TODO | /chat, POST /chat/message |
| `app/routers/dashboard_routes.py` | TODO | /dashboard, /trip/{id} |
| `app/email_service.py` | TODO | `send_trip_email(user, plan, png)` |
| `app/render.py` | TODO | `map_to_png(plan)` via Playwright |
| `app/main.py` | TODO | app factory, mounts, create_all |
| `templates/*.html` | TODO | frontend — once DONE, do NOT re-read |
| `static/css/style.css`, `static/js/chat.js` | TODO | frontend — once DONE, do NOT re-read |

## Frontend freeze policy
Once a `templates/` or `static/` file is `DONE`, treat it as frozen:
- Backend passes data via documented template context vars (list them beside each template
  when built). Agents render against the contract, they don't open the HTML.
- Only reopen a frozen frontend file if the USER asks for a visual/markup change.

## Why this saves tokens (rationale)
- A full re-read of all templates + CSS/JS per agent turn can cost thousands of tokens each.
  The ledger replaces that with ~1 line per file.
- Frontend is high-volume, low-churn → biggest win from freezing it.
- Fixed-facts block stops agents from re-reading `.env`/config to recall a var name.
- Net effect: agents load THIS file (~1–2 KB) instead of re-scanning the tree every turn.
