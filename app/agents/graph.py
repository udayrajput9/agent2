from langgraph.graph import StateGraph, START, END

from app.agents.nodes import (
    extract_intent,
    itinerary_planner,
    persist_plan,
    route_after_intent,
    run_activity_search,
    run_flight_search,
    run_hotel_search,
    send_plan_email,
)
from app.agents.state import TripState


def build_graph():
    graph = StateGraph(TripState)

    graph.add_node("extract_intent", extract_intent)
    graph.add_node("flight_search", run_flight_search)
    graph.add_node("hotel_search", run_hotel_search)
    graph.add_node("activity_search", run_activity_search)
    graph.add_node("itinerary_planner", itinerary_planner)
    graph.add_node("persist", persist_plan)
    graph.add_node("send_email", send_plan_email)

    graph.add_edge(START, "extract_intent")
    graph.add_conditional_edges(
        "extract_intent",
        route_after_intent,
        {"ask": END, "plan": "flight_search"},
    )
    graph.add_edge("flight_search", "hotel_search")
    graph.add_edge("hotel_search", "activity_search")
    graph.add_edge("activity_search", "itinerary_planner")
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
