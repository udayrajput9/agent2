# AI Trip Planner — Implementation Plan

> Prototype web app. Stack per spec, **agent pipeline built on LangChain + LangGraph** (deviation from spec's "plain Python orchestration").

## Env reconciliation (spec vs actual `.env`)

| Spec expects | Actual `.env` | Decision |
|---|---|---|
| `AVIATIONSTACK_API_KEY` | `AVIATIONSTACK_STACK_API_KEY` | Use actual var name |
| DB `trip_agent`, pw `1234` | `postgres` db, pw `postgres`, port `5433` | Use actual `DATABASE_URL` |
| `SMTP_HOST/PORT/USER/...` | `GMAIL_EMAIL` + `GMAIL_SMTP_PASSWORD` | Gmail SMTP `smtp.gmail.com:587` STARTTLS |
| `SECRET_KEY` | missing | **Add** for JWT signing |
| `GROQ_MODEL` | commented note only | **Add** `GROQ_MODEL=openai/gpt-oss-120b` |

## Stack
- Backend: FastAPI + Uvicorn
- Agents: LangGraph `StateGraph`; LangChain tools + `langchain-groq` `ChatGroq`
- DB: PostgreSQL via SQLAlchemy (`Base.metadata.create_all`, no Alembic)
- Frontend: Jinja2 + vanilla JS + CSS
- External APIs: Groq (`openai/gpt-oss-120b`), AviationStack (flights), Tavily (hotels/activities)
- Email: Gmail SMTP + inline `cid:` PNG
- Auth: bcrypt (`passlib`) + JWT in httpOnly cookie

## Dependencies (`requirements.txt`)
```
fastapi, uvicorn[standard], jinja2, python-multipart
sqlalchemy, psycopg2-binary
python-dotenv, pydantic, pydantic-settings
passlib[bcrypt], python-jose[cryptography]
langgraph, langchain, langchain-core, langchain-groq
langchain-community, tavily-python
requests, httpx
playwright   # server-side PNG render of the treasure map
```

## Folder structure
```
app/
├── main.py
├── config.py              # pydantic-settings loads .env
├── database.py
├── models.py              # User, TripPlan, ChatSession
├── auth.py                # bcrypt + JWT + get_current_user
├── routers/
│   ├── auth_routes.py
│   ├── chat_routes.py
│   └── dashboard_routes.py
├── agents/
│   ├── state.py           # TripState TypedDict (LangGraph shared state)
│   ├── graph.py           # StateGraph wiring: nodes + conditional edges
│   ├── nodes.py           # node fns (intent, plan, persist, email)
│   ├── tools.py           # @tool: flight_search, hotel_search, activity_search
│   ├── llm.py             # ChatGroq factory
│   └── prompts.py         # system prompts + JSON-schema instructions
├── email_service.py
├── render.py              # Playwright SVG->PNG
├── templates/
│   ├── signup.html, login.html, chat.html, dashboard.html
│   ├── partials/treasure_map.html
│   └── email_template.html
└── static/
    ├── css/style.css
    └── js/chat.js
.env, requirements.txt, README.md
```

## LangGraph pipeline
`TripState`: `user_id, raw_messages, source, destination, dates, duration_days, budget, preferences, missing_fields, questions, flights, hotels, activities, plan_json, status`

Graph:
```
extract_intent → [conditional: missing fields?]
    ├─ yes → ask_questions (END turn, return questions; cap 2–4)
    └─ no  → flight_search → hotel_search → activity_search
             → itinerary_planner → persist → send_email → END
```
- Tools are LangChain `@tool`, each try/except → `{}`/`[]` on failure (graceful degradation).
- `itinerary_planner` forces the fixed JSON schema (spec §5); Pydantic-validate before persist.
- Question loop is stateless across HTTP requests → partial intent persisted in `ChatSession.messages_json`, replayed each turn.

## DB schema
- `users`: id, email, username, hashed_password, created_at
- `trip_plans`: id, user_id FK, source, destination, budget, duration_days, plan_json, created_at
- `chat_sessions`: id, user_id, messages_json, status

## Treasure-map graph
SVG + CSS + light JS from `plan_json`: winding dashed `path`, per-day pin markers, hover popups (✈️🏨🍽️🎒🏆), parchment bg, budget bar. Reusable partial → also rendered to PNG (Playwright) for the email.

## Build phases
1. Skeleton + config + DB connect (`/health`).
2. Models + auth (signup→login→cookie→protected route).
3. LangGraph core: state, tools (test each standalone), graph end-to-end (full prompt = no questions; sparse prompt = asks questions).
4. Chat UI + routes.
5. Dashboard cards + treasure-map graph.
6. Server-side PNG (Playwright) + HTML email via Gmail SMTP, auto-triggered by `send_email` node.
7. Polish: CSS, loading states, error handling, README.

## Risks
1. Add `SECRET_KEY`, `GROQ_MODEL` to `.env` (Phase 1).
2. AviationStack free tier: use for airline/route data, LLM estimates costs when thin.
3. Playwright needs one-time `playwright install chromium`; fallback = Pillow/cairosvg.
4. LangGraph question loop stateless → replay from `ChatSession`.
