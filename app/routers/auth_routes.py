from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import COOKIE_NAME, create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/signup")
def signup_page(request: Request):
    if request.state.user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
def signup_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = User(email=email, username=username, hashed_password=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Username or email already taken."},
            status_code=400,
        )
    db.refresh(user)

    token = create_access_token(user.id, user.username)
    response = RedirectResponse("/chat", status_code=303)
    response.set_cookie(COOKIE_NAME, token, httponly=True, max_age=60 * 60 * 24 * 7)
    return response


@router.get("/login")
def login_page(request: Request):
    if request.state.user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password."},
            status_code=400,
        )

    token = create_access_token(user.id, user.username)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(COOKIE_NAME, token, httponly=True, max_age=60 * 60 * 24 * 7)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
