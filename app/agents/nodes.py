from app.agents.llm import get_llm
from app.agents.prompts import INTENT_SYSTEM_PROMPT, ITINERARY_SYSTEM_PROMPT, extract_json
from app.agents.state import TripState
from app.agents.tools import activity_search, flight_search, hotel_search

REQUIRED_FIELDS = ["source", "destination", "duration_days", "budget"]


def extract_intent(state: TripState) -> TripState:
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in state.get("messages", []))
    known = {
        "source": state.get("source"),
        "destination": state.get("destination"),
        "duration_days": state.get("duration_days"),
        "budget": state.get("budget"),
        "preferences": state.get("preferences"),
    }

    llm = get_llm(temperature=0.1, json_mode=True)
    messages = [
        {"role": "system", "content": INTENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Already known fields (json, may have nulls): {known}\n\nConversation:\n{convo}",
        },
    ]

    try:
        result = llm.invoke(messages)
        data = extract_json(result.content)
    except Exception:
        data = {}

    for field in ["source", "destination", "duration_days", "budget", "preferences"]:
        value = data.get(field)
        if value not in (None, ""):
            state[field] = value

    missing = [f for f in REQUIRED_FIELDS if not state.get(f)]
    state["missing_fields"] = missing

    if missing:
        questions = data.get("questions") or []
        state["questions"] = questions[:4]
        state["status"] = "need_info"
    else:
        state["questions"] = []
        state["status"] = "planning"

    return state


def route_after_intent(state: TripState) -> str:
    return "ask" if state.get("missing_fields") else "plan"


def run_flight_search(state: TripState) -> TripState:
    state["flights"] = flight_search.invoke(
        {"source": state["source"], "destination": state["destination"]}
    )
    return state


def run_hotel_search(state: TripState) -> TripState:
    state["hotels"] = hotel_search.invoke(
        {"destination": state["destination"], "budget": state.get("budget")}
    )
    return state


def run_activity_search(state: TripState) -> TripState:
    state["activities"] = activity_search.invoke(
        {"destination": state["destination"], "preferences": state.get("preferences")}
    )
    return state


def itinerary_planner(state: TripState) -> TripState:
    llm = get_llm(temperature=0.5, json_mode=True)
    context = {
        "source": state["source"],
        "destination": state["destination"],
        "duration_days": state["duration_days"],
        "budget": state["budget"],
        "preferences": state.get("preferences"),
        "flights_data": state.get("flights", []),
        "hotels_data": state.get("hotels", []),
        "activities_data": state.get("activities", []),
    }
    messages = [
        {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
        {"role": "user", "content": f"Trip data (json):\n{context}"},
    ]

    try:
        result = llm.invoke(messages)
        plan = extract_json(result.content)
    except Exception as exc:
        plan = {
            "source": state["source"],
            "destination": state["destination"],
            "duration_days": state["duration_days"],
            "total_budget": state["budget"],
            "budget_used": 0,
            "flights": [],
            "hotel": {},
            "days": [],
            "error_note": f"Itinerary generation failed: {exc}",
        }

    plan.setdefault("total_budget", state["budget"])
    plan.setdefault("budget_used", 0)
    plan.setdefault("source", state["source"])
    plan.setdefault("destination", state["destination"])
    plan.setdefault("duration_days", state["duration_days"])

    state["plan_json"] = plan
    return state


def persist_plan(state: TripState) -> TripState:
    from app.database import SessionLocal
    from app.models import TripPlan

    db = SessionLocal()
    try:
        trip = TripPlan(
            user_id=state["user_id"],
            source=state["source"],
            destination=state["destination"],
            budget=state["budget"],
            duration_days=state["duration_days"],
            plan_json=state["plan_json"],
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        state["trip_plan_id"] = trip.id
        state["status"] = "done"
    finally:
        db.close()
    return state


def send_plan_email(state: TripState) -> TripState:
    from app.database import SessionLocal
    from app.email_service import send_trip_email
    from app.models import TripPlan, User

    db = SessionLocal()
    try:
        user = db.get(User, state["user_id"])
        trip = db.get(TripPlan, state["trip_plan_id"])
        if user and trip:
            try:
                send_trip_email(user, trip)
            except Exception as exc:
                state["error"] = f"Email failed: {exc}"
    finally:
        db.close()
    return state
