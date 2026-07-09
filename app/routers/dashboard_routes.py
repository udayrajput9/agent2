from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TripPlan

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/login", status_code=303)

    trips = (
        db.query(TripPlan)
        .filter(TripPlan.user_id == request.state.user.id)
        .order_by(TripPlan.created_at.desc())
        .all()
    )
    return templates.TemplateResponse("dashboard.html", {"request": request, "trips": trips})


@router.get("/dashboard/{trip_id}")
def dashboard_trip_detail(trip_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/login", status_code=303)

    trips = (
        db.query(TripPlan)
        .filter(TripPlan.user_id == request.state.user.id)
        .order_by(TripPlan.created_at.desc())
        .all()
    )

    selected_trip = next((t for t in trips if t.id == trip_id), None)
    if not selected_trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    plan = dict(selected_trip.plan_json or {})
    plan.setdefault("id", selected_trip.id)
    plan.setdefault("destination", selected_trip.destination)

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "trips": trips, "selected_trip": selected_trip, "plan": plan},
    )
