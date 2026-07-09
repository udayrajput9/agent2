from typing import TypedDict, Optional, Any


class TripState(TypedDict, total=False):
    user_id: int
    chat_session_id: int
    messages: list[dict]  # [{"role": "user"|"bot", "content": str}]

    source: Optional[str]
    destination: Optional[str]
    duration_days: Optional[int]
    budget: Optional[float]
    preferences: Optional[str]

    missing_fields: list[str]
    questions: list[str]

    flights: list[dict]
    hotels: list[dict]
    activities: list[dict]

    plan_json: dict[str, Any]
    trip_plan_id: Optional[int]

    status: str  # "need_info" | "done" | "error"
    error: Optional[str]
