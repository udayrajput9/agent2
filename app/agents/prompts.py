import json
import re

INTENT_SYSTEM_PROMPT = """You are a trip-planning assistant. Read the conversation and extract trip \
essentials. Respond with ONLY a json object, no prose, matching exactly this schema:

{
  "source": string or null,
  "destination": string or null,
  "duration_days": integer or null,
  "budget": number or null,
  "preferences": string or null,
  "questions": array of up to 4 short strings
}

Rules:
- "questions" must contain ONLY questions for fields that are still missing/unclear \
(source, destination, duration_days, budget). Never re-ask for a field already given.
- If source, destination, budget, and duration_days are ALL already known from the \
conversation, "questions" MUST be an empty array [].
- Never output more than 4 questions total.
- preferences is optional (e.g. "adventure", "relaxing", "food", "family-friendly") - null if not mentioned.
- duration_days: if the user gives dates instead of a day count, compute the number of days.
"""

ITINERARY_SYSTEM_PROMPT = """You are a travel itinerary planner. Using the trip intent and the \
fetched flight/hotel/activity data below, produce a complete day-by-day itinerary that fits the \
stated budget. Respond with ONLY a json object, no prose, matching exactly this schema:

{
  "source": string,
  "destination": string,
  "duration_days": integer,
  "total_budget": number,
  "budget_used": number,
  "flights": [{"airline": string, "price": string, "departure": string, "arrival": string}],
  "hotel": {"name": string, "price_per_night": string, "rating": string, "address": string},
  "days": [
    {
      "day_number": integer,
      "title": string,
      "activities": [{"name": string}],
      "hotel": {"name": string},
      "estimated_cost": number
    }
  ]
}

Rules:
- "days" must have exactly duration_days entries, day_number starting at 1.
- budget_used must be your best-effort sum of estimated costs and must not exceed total_budget \
by more than a small margin; if input data is sparse, use reasonable real-world estimates and \
note that in an activity name (e.g. "Estimated - Museum visit").
- If flight or hotel data is missing/empty, still produce a plausible entry based on general \
knowledge and mark it as an estimate.
"""


def extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)
