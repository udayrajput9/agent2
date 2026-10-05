import requests
from langchain_core.tools import tool
from tavily import TavilyClient

from app.config import settings

AVIATIONSTACK_URL = "http://api.aviationstack.com/v1/flights"


def _tavily_client() -> TavilyClient:
    return TavilyClient(api_key=settings.TAVILY_API_KEY)


def _tavily_results(query: str, max_results: int = 5) -> list[dict]:
    try:
        result = _tavily_client().search(query=query, max_results=max_results)
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:500]}
            for r in result.get("results", [])
        ]
    except Exception:
        return []


def _aviationstack_schedule(source: str, destination: str) -> list[dict]:
    """Live schedule data, only useful when at least one endpoint is an IATA code."""
    params = {"access_key": settings.AVIATIONSTACK_STACK_API_KEY, "limit": 5}
    if len(source.strip()) == 3:
        params["dep_iata"] = source.strip().upper()
    if len(destination.strip()) == 3:
        params["arr_iata"] = destination.strip().upper()
    if "dep_iata" not in params and "arr_iata" not in params:
        return []

    try:
        resp = requests.get(AVIATIONSTACK_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception:
        return []

    return [
        {
            "airline": (item.get("airline") or {}).get("name", "Unknown"),
            "departure": (item.get("departure") or {}).get("scheduled", ""),
            "arrival": (item.get("arrival") or {}).get("scheduled", ""),
        }
        for item in data
    ]


@tool
def flight_search(
    source: str,
    destination: str,
    travel_date: str | None = None,
    return_date: str | None = None,
) -> dict:
    """Research flight ticket prices for the trip via Tavily web search:
    the outbound fare on the given travel date and the return fare on the
    return date, plus live schedule data from AviationStack when IATA codes
    are given. Returns {"outbound_prices", "return_prices", "live_schedule"}."""
    outbound_query = f"flight ticket price from {source} to {destination}"
    if travel_date:
        outbound_query += f" on {travel_date}"
    outbound_query += " airlines and cheapest fare"

    results = {
        "outbound_prices": _tavily_results(outbound_query),
        "return_prices": [],
        "live_schedule": _aviationstack_schedule(source, destination),
    }

    if return_date or travel_date:
        return_query = f"return flight ticket price from {destination} to {source}"
        if return_date:
            return_query += f" on {return_date}"
        return_query += " airlines and cheapest fare"
        results["return_prices"] = _tavily_results(return_query)

    return results


@tool
def hotel_search(destination: str, budget: float | None = None, currency_symbol: str = "$") -> list[dict]:
    """Research stay prices across every tier via Tavily - OYO/budget hotels,
    guest houses, local homestays, and premium hotels - so the planner gets
    5-10 price points per night to compare against the budget.
    Returns a list of {tier, title, url, content} dicts, or [] on failure."""
    budget_hint = f" within total trip budget {currency_symbol}{budget}" if budget else ""
    tier_queries = [
        ("budget/OYO", f"OYO rooms and cheap budget hotels in {destination} price per night{budget_hint}"),
        ("guest house/homestay", f"guest house and local homestay in {destination} price per night and rating"),
        ("premium", f"best premium hotels in {destination} price per night and rating"),
    ]

    results = []
    for tier, query in tier_queries:
        for r in _tavily_results(query, max_results=4):
            results.append({"tier": tier, **r})
    return results[:10]


@tool
def transport_search(destination: str) -> list[dict]:
    """Research local transportation prices at the destination via Tavily -
    cab/taxi (Ola/Uber), bike taxi (Rapido), auto rickshaw, and public
    transport (bus/metro) fares - giving 5-10 price points to compare.
    Returns a list of {mode, title, url, content} dicts, or [] on failure."""
    mode_queries = [
        ("cab/taxi", f"Ola Uber taxi cab fare per km and airport transfer price in {destination}"),
        ("bike/auto", f"Rapido bike taxi and auto rickshaw fare per km in {destination}"),
        ("public transport", f"local bus metro fares and daily travel pass price in {destination}"),
    ]

    results = []
    for mode, query in mode_queries:
        for r in _tavily_results(query, max_results=4):
            results.append({"mode": mode, **r})
    return results[:10]


@tool
def activity_search(destination: str, preferences: str | None = None) -> list[dict]:
    """Search Tavily for things to do, attractions, and food spots at the destination.
    Returns a list of {title, url, content} dicts, or [] on failure."""
    query = f"top attractions, things to do, and food spots in {destination}"
    if preferences:
        query += f" for a {preferences} trip"
    return _tavily_results(query)


@tool
def weather_search(destination: str) -> list[dict]:
    """Search OpenWeatherMap for the 5-day weather forecast at the destination.
    Returns a list of daily summarized weather forecasts."""
    if not settings.OPENWEATHERMAP_API_KEY:
        return []

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": destination,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric"
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # OpenWeather returns 3-hour chunks for 5 days (40 items).
        # We'll group them by day and pick the midday weather or just a summary.
        daily_weather = {}
        for item in data.get("list", []):
            dt_txt = item.get("dt_txt", "")
            if not dt_txt:
                continue
            date_str = dt_txt.split(" ")[0]

            # Prefer 12:00:00 time for the day's primary weather
            if date_str not in daily_weather or "12:00:00" in dt_txt:
                temp = item.get("main", {}).get("temp", "Unknown")
                desc = item.get("weather", [{}])[0].get("description", "Unknown")
                daily_weather[date_str] = {"date": date_str, "temp_c": temp, "description": desc}

        return list(daily_weather.values())[:5]
    except Exception:
        return []
