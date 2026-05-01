from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.i18n import SUPPORTED_LANGS, get_lang, get_templates, gettext_for
from app.models.user import User
from app.routers.auth import check_password_strength, hash_password, verify_password

router = APIRouter()


def _require_page_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=302, detail="Not authenticated", headers={"location": "/login"}
        )
    return user_id


@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request, db: Session = Depends(get_db)):
    user_id = _require_page_user(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return get_templates(request).TemplateResponse(
        request,
        "account.html",
        {
            "user": user,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language": user.language,
            "error": None,
        },
    )


@router.post("/account", response_class=HTMLResponse)
def update_account(
    request: Request,
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    language: str = Form(default=""),
    current_password: str = Form(default=""),
    new_password: str = Form(default=""),
    new_password_confirm: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user_id = _require_page_user(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)

    _ = lambda s: gettext_for(request, s)  # noqa: E731

    first_name = first_name.strip()
    last_name = last_name.strip()

    def _error(msg: str) -> HTMLResponse:
        return get_templates(request).TemplateResponse(
            request,
            "account.html",
            {
                "user": user,
                "first_name": first_name,
                "last_name": last_name,
                "language": language,
                "error": msg,
            },
            status_code=400,
        )

    if not first_name:
        return _error(_("First name is required."))
    if not last_name:
        return _error(_("Last name is required."))
    if language not in SUPPORTED_LANGS:
        return _error(_("Invalid language."))

    pw_fields = (current_password, new_password, new_password_confirm)
    if any(pw_fields):
        if not all(pw_fields):
            return _error(_("All password fields are required to change your password"))
        if not verify_password(current_password, user.hashed_password):
            return _error(_("Current password is incorrect"))
        if new_password != new_password_confirm:
            return _error(_("Passwords do not match"))
        strength_error = check_password_strength(
            new_password, user_inputs=[first_name, last_name, user.email]
        )
        if strength_error:
            return _error(strength_error)
        user.hashed_password = hash_password(new_password)

    user.first_name = first_name
    user.last_name = last_name
    user.language = language
    db.commit()

    request.session["first_name"] = first_name
    request.session["lang"] = language

    return RedirectResponse("/dashboard", status_code=302)
