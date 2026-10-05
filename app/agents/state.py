from typing import TypedDict, Optional, Any


class TripState(TypedDict, total=False):
    user_id: int
    chat_session_id: int
    messages: list[dict]  # [{"role": "user"|"bot", "content": str}]

    source: Optional[str]
    destination: Optional[str]
    duration_days: Optional[int]
    budget: Optional[float]
    currency_symbol: Optional[str]
    travel_date: Optional[str]
    return_date: Optional[str]
    preferences: Optional[str]

    missing_fields: list[str]
    questions: list[str]

    flights: dict[str, Any]  # {"outbound_prices": [...], "return_prices": [...], "live_schedule": [...]}
    hotels: list[dict]
    activities: list[dict]
    weather_data: list[dict]
    transport: list[dict]

    budget_plan: dict[str, Any]

    plan_json: dict[str, Any]
    trip_plan_id: Optional[int]

    status: str  # "need_info" | "done" | "error"
    error: Optional[str]
