from langchain_core.runnables import Runnable
from langgraph.graph import END

from app.agents.llm import get_llm
from app.agents.prompts import (
    BUDGET_SYSTEM_PROMPT,
    INTENT_SYSTEM_PROMPT,
    ITINERARY_SYSTEM_PROMPT,
    extract_json,
)
from app.agents.state import TripState
from app.agents.tools import (
    activity_search,
    flight_search,
    hotel_search,
    transport_search,
    weather_search,
)

REQUIRED_FIELDS = ["source", "destination", "duration_days", "budget"]

SEARCH_NODES = ["flight_search", "hotel_search", "activity_search", "weather_search", "transport_search"]


def _invoke_json(llm: Runnable, messages: list[dict], retries: int = 1) -> dict:
    """Invoke the llm and parse json from the reply, re-prompting once on bad json."""
    last_exc: Exception | None = None
    for _ in range(retries + 1):
        result = llm.invoke(messages)
        try:
            return extract_json(result.content)
        except Exception as exc:
            last_exc = exc
            messages = messages + [
                {"role": "assistant", "content": result.content},
                {
                    "role": "user",
                    "content": "That response was not valid JSON. Respond again with ONLY the valid json object, nothing else.",
                },
            ]
    raise last_exc


def extract_intent(state: TripState) -> dict:
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
        data = _invoke_json(llm, messages)
    except Exception:
        data = {}

    updates: dict = {}
    for field in ["source", "destination", "duration_days", "budget", "currency_symbol", "travel_date", "return_date", "preferences"]:
        value = data.get(field)
        if value not in (None, ""):
            updates[field] = value

    merged = {**state, **updates}
    missing = [f for f in REQUIRED_FIELDS if not merged.get(f)]
    updates["missing_fields"] = missing

    if missing:
        updates["questions"] = (data.get("questions") or [])[:4]
        updates["status"] = "need_info"
    else:
        updates["questions"] = []
        updates["status"] = "planning"

    return updates


def route_after_intent(state: TripState):
    if state.get("missing_fields"):
        return END
    # Fan out: run all searches in parallel, then join at the itinerary planner.
    return SEARCH_NODES


def run_flight_search(state: TripState) -> dict:
    return {
        "flights": flight_search.invoke(
            {
                "source": state["source"],
                "destination": state["destination"],
                "travel_date": state.get("travel_date"),
                "return_date": state.get("return_date"),
            }
        )
    }


def run_hotel_search(state: TripState) -> dict:
    kwargs = {"destination": state["destination"], "budget": state.get("budget")}
    if state.get("currency_symbol"):
        kwargs["currency_symbol"] = state["currency_symbol"]
    return {"hotels": hotel_search.invoke(kwargs)}


def run_activity_search(state: TripState) -> dict:
    return {
        "activities": activity_search.invoke(
            {"destination": state["destination"], "preferences": state.get("preferences")}
        )
    }


def run_weather_search(state: TripState) -> dict:
    return {"weather_data": weather_search.invoke({"destination": state["destination"]})}


def run_transport_search(state: TripState) -> dict:
    return {"transport": transport_search.invoke({"destination": state["destination"]})}


def budget_planner(state: TripState) -> dict:
    """Finance agent: compares researched prices and allocates the budget."""
    llm = get_llm(temperature=0.2, json_mode=True)
    context = {
        "total_budget": state["budget"],
        "currency_symbol": state.get("currency_symbol") or "$",
        "duration_days": state["duration_days"],
        "travel_date": state.get("travel_date"),
        "return_date": state.get("return_date"),
        "preferences": state.get("preferences"),
        "flights_research": state.get("flights", {}),
        "stays_research": state.get("hotels", []),
        "transport_research": state.get("transport", []),
    }
    messages = [
        {"role": "system", "content": BUDGET_SYSTEM_PROMPT},
        {"role": "user", "content": f"Budget and researched prices (json):\n{context}"},
    ]

    try:
        budget_plan = _invoke_json(llm, messages)
    except Exception:
        budget_plan = {}

    return {"budget_plan": budget_plan}


def itinerary_planner(state: TripState) -> dict:
    llm = get_llm(temperature=0.5, json_mode=True)
    context = {
        "source": state["source"],
        "destination": state["destination"],
        "duration_days": state["duration_days"],
        "budget": state["budget"],
        "travel_date": state.get("travel_date"),
        "return_date": state.get("return_date"),
        "preferences": state.get("preferences"),
        "chat_history": "\n".join(f"{m['role']}: {m['content']}" for m in state.get("messages", [])),
        "flights_data": state.get("flights", {}),
        "hotels_data": state.get("hotels", []),
        "activities_data": state.get("activities", []),
        "weather_data": state.get("weather_data", []),
        "transport_data": state.get("transport", []),
        "budget_plan": state.get("budget_plan", {}),
    }
    messages = [
        {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
        {"role": "user", "content": f"Trip data (json):\n{context}"},
    ]

    try:
        plan = _invoke_json(llm, messages)
    except Exception as exc:
        plan = {
            "source": state["source"],
            "destination": state["destination"],
            "duration_days": state["duration_days"],
            "total_budget": state["budget"],
            "budget_used": 0,
            "currency_symbol": state.get("currency_symbol") or "$",
            "currency_code": "USD" if not state.get("currency_symbol") else "N/A",
            "weather": "Unknown",
            "tips": [],
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

    # Carry the finance agent's comparison into the stored plan so the
    # dashboard can render the price tables and strategies.
    if state.get("budget_plan"):
        plan["budget_plan"] = state["budget_plan"]

    return {"plan_json": plan}


def persist_plan(state: TripState) -> dict:
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
        return {"trip_plan_id": trip.id, "status": "done"}
    finally:
        db.close()


def send_plan_email(state: TripState) -> dict:
    from app.database import SessionLocal
    from app.email_service import send_trip_email
    from app.models import TripPlan, User

    db = SessionLocal()
    try:
        user = db.get(User, state["user_id"])
        trip = db.get(TripPlan, state["trip_plan_id"])
        if user and trip:
            plan = trip.plan_json or {}
            if plan.get("error_note") or not plan.get("days"):
                # Do not send email if the plan failed to generate perfectly
                return {}

            try:
                send_trip_email(user, trip)
            except Exception as exc:
                return {"error": f"Email failed: {exc}"}
    finally:
        db.close()
    return {}
