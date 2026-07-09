from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth import COOKIE_NAME, get_user_from_token
from app.database import Base, engine, SessionLocal
from app.routers import auth_routes, chat_routes, dashboard_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Trip Planner")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


class CurrentUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(COOKIE_NAME)
        db = SessionLocal()
        try:
            request.state.user = get_user_from_token(db, token)
        finally:
            db.close()
        return await call_next(request)


app.add_middleware(CurrentUserMiddleware)

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(dashboard_routes.router)


@app.get("/")
def root(request: Request):
    from fastapi.responses import RedirectResponse

    if request.state.user:
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/login", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}
