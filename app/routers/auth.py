from pathlib import Path

import bcrypt
import zxcvbn as zxcvbn_lib
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

MIN_PASSWORD_SCORE = 2  # 0-4; 2 = "fair"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def check_password_strength(password: str, user_inputs: list[str]) -> str | None:
    """Return an error message if the password is too weak, else None."""
    result = zxcvbn_lib.zxcvbn(password, user_inputs=user_inputs)
    if result["score"] < MIN_PASSWORD_SCORE:
        feedback = result["feedback"]
        warning = feedback.get("warning") or "Password is too weak."
        suggestions = feedback.get("suggestions", [])
        message = warning
        if suggestions:
            message += " " + suggestions[0]
        return message
    return None


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Invalid email or password"}, status_code=401
        )
    request.session["user_id"] = user.id
    request.session["first_name"] = user.first_name
    return RedirectResponse("/", status_code=302)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, "register.html", {"error": None})


@router.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    if password != password_confirm:
        return templates.TemplateResponse(
            request, "register.html", {"error": "Passwords do not match"}, status_code=400
        )
    strength_error = check_password_strength(password, user_inputs=[first_name, last_name, email])
    if strength_error:
        return templates.TemplateResponse(
            request, "register.html", {"error": strength_error}, status_code=400
        )
    if db.query(User).filter(User.email == email.lower()).first():
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": "An account with this email already exists"},
            status_code=400,
        )
    user = User(
        email=email.lower(),
        first_name=first_name,
        last_name=last_name,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    request.session["first_name"] = user.first_name
    return RedirectResponse("/", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
