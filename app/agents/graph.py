from langgraph.graph import StateGraph, START, END

from app.agents.nodes import (
    SEARCH_NODES,
    budget_planner,
    extract_intent,
    itinerary_planner,
    persist_plan,
    route_after_intent,
    run_activity_search,
    run_flight_search,
    run_hotel_search,
    run_transport_search,
    run_weather_search,
    send_plan_email,
)
from app.agents.state import TripState


def build_graph():
    graph = StateGraph(TripState)

    graph.add_node("extract_intent", extract_intent)
    graph.add_node("flight_search", run_flight_search)
    graph.add_node("hotel_search", run_hotel_search)
    graph.add_node("activity_search", run_activity_search)
    graph.add_node("weather_search", run_weather_search)
    graph.add_node("transport_search", run_transport_search)
    graph.add_node("budget_planner", budget_planner)
    graph.add_node("itinerary_planner", itinerary_planner)
    graph.add_node("persist", persist_plan)
    graph.add_node("send_email", send_plan_email)

    graph.add_edge(START, "extract_intent")
    # Either stop to ask the user for missing info, or fan out to all
    # searches at once; the finance agent waits for every branch, decides
    # the budget split, then the itinerary planner builds the plan on it.
    graph.add_conditional_edges(
        "extract_intent",
        route_after_intent,
        SEARCH_NODES + [END],
    )
    for node in SEARCH_NODES:
        graph.add_edge(node, "budget_planner")
    graph.add_edge("budget_planner", "itinerary_planner")
    graph.add_edge("itinerary_planner", "persist")
    graph.add_edge("persist", "send_email")
    graph.add_edge("send_email", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
