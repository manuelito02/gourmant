from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.i18n import get_templates, gettext_for
from app.models.recipe import Recipe
from app.models.user import User, UserRole

router = APIRouter(prefix="/admin")


def _require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=302, detail="Not authenticated", headers={"location": "/login"}
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _count_admins(db: Session) -> int:
    return db.query(User).filter(User.role == UserRole.ADMIN).count()


@router.get("/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    recipe_counts = dict(
        db.query(Recipe.user_id, func.count(Recipe.id)).group_by(Recipe.user_id).all()
    )
    users = db.query(User).order_by(User.created_at.desc()).all()
    admin_count = sum(1 for u in users if u.role == UserRole.ADMIN)
    return get_templates(request).TemplateResponse(
        request,
        "admin/users.html",
        {"users": users, "recipe_counts": recipe_counts, "admin_count": admin_count},
    )


@router.post("/users/{user_id}/role", response_class=HTMLResponse)
def toggle_role(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)

    _ = lambda s: gettext_for(request, s)  # noqa: E731

    if target.role == UserRole.ADMIN and _count_admins(db) <= 1:
        raise HTTPException(status_code=400, detail=_("Cannot remove the last admin role."))

    target.role = UserRole.USER if target.role == UserRole.ADMIN else UserRole.ADMIN
    db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)
    return get_templates(request).TemplateResponse(
        request,
        "admin/user_edit.html",
        {"target": target},
    )


@router.post("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user(
    user_id: int,
    request: Request,
    role: str = Form(...),
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)

    _ = lambda s: gettext_for(request, s)  # noqa: E731

    new_role = UserRole.ADMIN if role == "admin" else UserRole.USER
    if target.role == UserRole.ADMIN and new_role == UserRole.USER and _count_admins(db) <= 1:
        raise HTTPException(status_code=400, detail=_("Cannot remove the last admin role."))

    target.role = new_role
    db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/users/{user_id}/delete", response_class=HTMLResponse)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)

    _ = lambda s: gettext_for(request, s)  # noqa: E731

    if target.id == admin.id:
        raise HTTPException(status_code=400, detail=_("Cannot delete your own account."))
    if target.role == UserRole.ADMIN and _count_admins(db) <= 1:
        raise HTTPException(status_code=400, detail=_("Cannot delete the last admin."))

    db.delete(target)
    db.commit()
    return RedirectResponse("/admin/users", status_code=302)
