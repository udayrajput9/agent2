import requests
from langchain_core.tools import tool
from tavily import TavilyClient

from app.config import settings

AVIATIONSTACK_URL = "http://api.aviationstack.com/v1/flights"


@tool
def flight_search(source: str, destination: str) -> list[dict]:
    """Look up flights between source and destination via AviationStack.
    Returns a list of flight dicts, or [] if no data could be fetched."""
    params = {"access_key": settings.AVIATIONSTACK_STACK_API_KEY, "limit": 5}

    if len(source.strip()) == 3:
        params["dep_iata"] = source.strip().upper()
    if len(destination.strip()) == 3:
        params["arr_iata"] = destination.strip().upper()

    try:
        resp = requests.get(AVIATIONSTACK_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception:
        return []

    flights = []
    for item in data:
        airline = (item.get("airline") or {}).get("name", "Unknown")
        departure = (item.get("departure") or {}).get("scheduled", "")
        arrival = (item.get("arrival") or {}).get("scheduled", "")
        flights.append(
            {
                "airline": airline,
                "price": "estimate",
                "departure": departure,
                "arrival": arrival,
            }
        )
    return flights


def _tavily_client() -> TavilyClient:
    return TavilyClient(api_key=settings.TAVILY_API_KEY)


@tool
def hotel_search(destination: str, budget: float | None = None) -> list[dict]:
    """Search Tavily for hotels near the destination within budget.
    Returns a list of {title, url, content} dicts, or [] on failure."""
    query = f"best rated hotels to stay in {destination}"
    if budget:
        query += f" within budget ${budget}"
    try:
        result = _tavily_client().search(query=query, max_results=5)
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:500]}
            for r in result.get("results", [])
        ]
    except Exception:
        return []


@tool
def activity_search(destination: str, preferences: str | None = None) -> list[dict]:
    """Search Tavily for things to do, attractions, and food spots at the destination.
    Returns a list of {title, url, content} dicts, or [] on failure."""
    query = f"top attractions, things to do, and food spots in {destination}"
    if preferences:
        query += f" for a {preferences} trip"
    try:
        result = _tavily_client().search(query=query, max_results=5)
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:500]}
            for r in result.get("results", [])
        ]
    except Exception:
        return []
