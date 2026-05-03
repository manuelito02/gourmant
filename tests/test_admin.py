from app.config import settings as app_settings
from app.models.user import User, UserRole

REGULAR_USER = {
    "first_name": "Regular",
    "last_name": "User",
    "email": "regular@example.com",
    "password": "correct-horse-battery-staple",
    "password_confirm": "correct-horse-battery-staple",
}

SECOND_ADMIN = {
    "first_name": "Second",
    "last_name": "Admin",
    "email": "second-admin@example.com",
    "password": "correct-horse-battery-staple",
    "password_confirm": "correct-horse-battery-staple",
}


def _get_user(db, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def _create_user_db(db, data: dict) -> User:
    """Insert a user directly via DB — avoids touching the HTTP client session."""
    from app.routers.auth import hash_password as hp

    user = User(
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        hashed_password=hp(data["password"]),
        language="en",
    )
    db.add(user)
    db.commit()
    db.expire(user)
    return user


def _promote_db(db, user: User) -> None:
    user.role = UserRole.ADMIN
    db.commit()
    db.expire(user)


# ── Auth gates ────────────────────────────────────────────────────────────────


def test_anon_get_admin_users_redirects_to_login(client):
    response = client.get("/admin/users")
    assert response.url.path == "/login"


def test_non_admin_get_admin_users_returns_403(auth_client):
    response = auth_client.get("/admin/users")
    assert response.status_code == 403


def test_anon_get_edit_redirects_to_login(client):
    response = client.get("/admin/users/9999/edit")
    assert response.url.path == "/login"


def test_non_admin_get_edit_returns_403(auth_client):
    response = auth_client.get("/admin/users/9999/edit")
    assert response.status_code == 403


def test_anon_post_edit_redirects_to_login(client):
    response = client.post("/admin/users/9999/edit", data={"role": "user"})
    assert response.url.path == "/login"


def test_non_admin_post_edit_returns_403(auth_client):
    response = auth_client.post("/admin/users/9999/edit", data={"role": "user"})
    assert response.status_code == 403


def test_anon_post_delete_redirects_to_login(client):
    response = client.post("/admin/users/9999/delete")
    assert response.url.path == "/login"


def test_non_admin_post_delete_returns_403(auth_client):
    response = auth_client.post("/admin/users/9999/delete")
    assert response.status_code == 403


# ── GET /admin/users ──────────────────────────────────────────────────────────


def test_admin_users_list_has_back_button(admin_client):
    response = admin_client.get("/admin/users")
    assert response.status_code == 200
    assert "/dashboard" in response.text


def test_admin_sees_user_list(admin_client, db):
    _create_user_db(db, REGULAR_USER)
    response = admin_client.get("/admin/users")
    assert response.status_code == 200
    assert REGULAR_USER["email"] in response.text
    assert app_settings.admin_email in response.text


# ── GET /admin/users/{id}/edit ────────────────────────────────────────────────


def test_admin_get_edit_renders_form(admin_client, db):
    regular = _create_user_db(db, REGULAR_USER)
    response = admin_client.get(f"/admin/users/{regular.id}/edit")
    assert response.status_code == 200
    assert REGULAR_USER["email"] in response.text
    assert 'name="role"' in response.text


def test_get_edit_nonexistent_user_returns_404(admin_client):
    response = admin_client.get("/admin/users/999999/edit")
    assert response.status_code == 404


# ── POST /admin/users/{id}/edit ───────────────────────────────────────────────


def test_admin_promotes_regular_user(admin_client, db):
    regular = _create_user_db(db, REGULAR_USER)
    admin_client.post(f"/admin/users/{regular.id}/edit", data={"role": "admin"})
    db.expire_all()
    assert _get_user(db, REGULAR_USER["email"]).role == UserRole.ADMIN


def test_admin_demotes_another_admin(admin_client, db):
    second = _create_user_db(db, SECOND_ADMIN)
    _promote_db(db, second)
    admin_client.post(f"/admin/users/{second.id}/edit", data={"role": "user"})
    db.expire_all()
    assert _get_user(db, SECOND_ADMIN["email"]).role == UserRole.USER


# ── Last-admin protection ─────────────────────────────────────────────────────


def test_last_admin_cannot_demote_self(admin_client, db):
    admin = _get_user(db, app_settings.admin_email)
    response = admin_client.post(f"/admin/users/{admin.id}/edit", data={"role": "user"})
    assert response.status_code == 400
    db.expire_all()
    assert _get_user(db, app_settings.admin_email).role == UserRole.ADMIN


def test_last_admin_cannot_delete_self(admin_client, db):
    admin = _get_user(db, app_settings.admin_email)
    response = admin_client.post(f"/admin/users/{admin.id}/delete")
    assert response.status_code == 400
    db.expire_all()
    assert _get_user(db, app_settings.admin_email) is not None


# ── Delete ────────────────────────────────────────────────────────────────────


def test_admin_deletes_regular_user_and_cascades_recipes(admin_client, db, ref):
    from app.models.recipe import Recipe

    regular = _create_user_db(db, REGULAR_USER)
    # Add a recipe directly in DB to verify cascade
    recipe = Recipe(user_id=regular.id, title="To be deleted", type_id=ref["type_id"])
    db.add(recipe)
    db.commit()
    user_id = regular.id

    response = admin_client.post(f"/admin/users/{user_id}/delete")
    assert response.url.path == "/admin/users"
    db.expire_all()
    assert _get_user(db, REGULAR_USER["email"]) is None
    assert db.query(Recipe).filter(Recipe.user_id == user_id).count() == 0


def test_admin_cannot_delete_self(admin_client, db):
    admin = _get_user(db, app_settings.admin_email)
    response = admin_client.post(f"/admin/users/{admin.id}/delete")
    assert response.status_code == 400


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_edit_nonexistent_user_returns_404(admin_client):
    response = admin_client.post("/admin/users/999999/edit", data={"role": "user"})
    assert response.status_code == 404


def test_delete_nonexistent_user_returns_404(admin_client):
    response = admin_client.post("/admin/users/999999/delete")
    assert response.status_code == 404


# ── Session role seeded on login ──────────────────────────────────────────────


def test_admin_nav_link_visible_to_admin(admin_client):
    response = admin_client.get("/dashboard")
    assert "admin" in response.text.lower()


def test_admin_nav_link_hidden_from_regular_user(auth_client):
    response = auth_client.get("/dashboard")
    assert "/admin/users" not in response.text
