from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.graph import get_graph
from app.agents.state import TripState
from app.database import get_db
from app.models import ChatSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

INTENT_FIELDS = ["source", "destination", "duration_days", "budget", "preferences"]


def _get_active_session(db: Session, user_id: int) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id, ChatSession.status == "active")
        .order_by(ChatSession.id.desc())
        .first()
    )
    if not session:
        session = ChatSession(user_id=user_id, messages_json=[], intent_json={}, status="active")
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


@router.get("/chat")
def chat_page(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/login", status_code=303)

    session = _get_active_session(db, request.state.user.id)
    return templates.TemplateResponse(
        "chat.html", {"request": request, "messages": session.messages_json}
    )


class ChatMessageIn(BaseModel):
    message: str


@router.post("/api/chat")
def chat_message(payload: ChatMessageIn, request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        raise HTTPException(status_code=401, detail="Please log in to continue.")

    user = request.state.user
    session = _get_active_session(db, user.id)

    messages = list(session.messages_json or [])
    messages.append({"role": "user", "content": payload.message})

    state: TripState = {
        "user_id": user.id,
        "chat_session_id": session.id,
        "messages": messages,
        **(session.intent_json or {}),
    }

    try:
        graph = get_graph()
        result = graph.invoke(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Planning failed: {exc}")

    session.intent_json = {field: result.get(field) for field in INTENT_FIELDS}

    if result.get("status") == "done":
        session.messages_json = messages
        session.status = "completed"
        db.commit()
        return {"redirect_url": f"/dashboard/{result['trip_plan_id']}"}

    questions = result.get("questions") or []
    if not questions:
        questions = ["Could you share a bit more detail about your trip?"]

    for q in questions:
        messages.append({"role": "bot", "content": q})

    session.messages_json = messages
    db.commit()

    return {"messages": [{"role": "bot", "content": q} for q in questions]}
