from app.models.user import User
from app.routers.auth import verify_password

VALID_USER = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "password": "correct-horse-battery-staple",
    "password_confirm": "correct-horse-battery-staple",
}


def _get_user(db, email: str = VALID_USER["email"]) -> User:
    return db.query(User).filter(User.email == email).first()


def _register(client):
    client.post("/register", data=VALID_USER)


def _account_payload(**overrides) -> dict:
    base = {
        "first_name": VALID_USER["first_name"],
        "last_name": VALID_USER["last_name"],
        "language": "en",
        "current_password": "",
        "new_password": "",
        "new_password_confirm": "",
    }
    base.update(overrides)
    return base


# ── Auth gate ─────────────────────────────────────────────────────────────────


def test_account_requires_auth(client):
    response = client.get("/account")
    assert response.url.path == "/login"


def test_account_post_requires_auth(client):
    response = client.post("/account", data=_account_payload())
    assert response.url.path == "/login"


# ── GET /account ──────────────────────────────────────────────────────────────


def test_account_page_shows_email(client):
    _register(client)
    response = client.get("/account")
    assert response.status_code == 200
    assert VALID_USER["email"] in response.text


def test_account_page_shows_current_name(client):
    _register(client)
    response = client.get("/account")
    assert VALID_USER["first_name"] in response.text
    assert VALID_USER["last_name"] in response.text


# ── POST /account — profile fields ────────────────────────────────────────────


def test_account_update_name(client, db):
    _register(client)
    response = client.post("/account", data=_account_payload(first_name="Alice", last_name="New"))
    assert response.url.path == "/dashboard"
    db.expire_all()
    user = _get_user(db)
    assert user.first_name == "Alice"
    assert user.last_name == "New"


def test_account_update_language(client, db):
    _register(client)
    client.post("/account", data=_account_payload(language="fr"))
    db.expire_all()
    user = _get_user(db)
    assert user.language == "fr"


def test_account_update_language_updates_session(client, db):
    _register(client)
    client.post("/account", data=_account_payload(language="fr"))
    response = client.get("/dashboard")
    assert "Recettes" in response.text


def test_account_empty_first_name_rejected(client):
    _register(client)
    response = client.post("/account", data=_account_payload(first_name="   "))
    assert response.status_code == 400


def test_account_empty_last_name_rejected(client):
    _register(client)
    response = client.post("/account", data=_account_payload(last_name=""))
    assert response.status_code == 400


def test_account_invalid_language_rejected(client):
    _register(client)
    response = client.post("/account", data=_account_payload(language="xx"))
    assert response.status_code == 400


# ── POST /account — password change ───────────────────────────────────────────


def test_account_change_password(client, db):
    _register(client)
    new_pw = "purple-monkey-dishwasher-99"
    client.post(
        "/account",
        data=_account_payload(
            current_password=VALID_USER["password"],
            new_password=new_pw,
            new_password_confirm=new_pw,
        ),
    )
    db.expire_all()
    user = _get_user(db)
    assert verify_password(new_pw, user.hashed_password)


def test_account_wrong_current_password_rejected(client):
    _register(client)
    new_pw = "purple-monkey-dishwasher-99"
    response = client.post(
        "/account",
        data=_account_payload(
            current_password="wrong-password",
            new_password=new_pw,
            new_password_confirm=new_pw,
        ),
    )
    assert response.status_code == 400
    assert "incorrect" in response.text.lower()


def test_account_passwords_dont_match(client):
    _register(client)
    response = client.post(
        "/account",
        data=_account_payload(
            current_password=VALID_USER["password"],
            new_password="purple-monkey-dishwasher-99",
            new_password_confirm="different-password-here",
        ),
    )
    assert response.status_code == 400


def test_account_new_password_too_weak(client):
    _register(client)
    response = client.post(
        "/account",
        data=_account_payload(
            current_password=VALID_USER["password"],
            new_password="abc",
            new_password_confirm="abc",
        ),
    )
    assert response.status_code == 400


def test_account_partial_password_fields_rejected(client):
    _register(client)
    response = client.post(
        "/account",
        data=_account_payload(
            current_password=VALID_USER["password"],
            new_password="purple-monkey-dishwasher-99",
            new_password_confirm="",
        ),
    )
    assert response.status_code == 400


def test_account_empty_password_fields_allowed(client, db):
    _register(client)
    original_hash = _get_user(db).hashed_password
    response = client.post("/account", data=_account_payload())
    assert response.url.path == "/dashboard"
    db.expire_all()
    assert _get_user(db).hashed_password == original_hash


# ── Login seeds lang from user preference ─────────────────────────────────────


def test_login_seeds_lang_from_user(client, db):
    _register(client)
    # Set language to French via account update
    client.post("/account", data=_account_payload(language="fr"))
    # Log out, then log in again
    client.post("/logout")
    client.post("/login", data={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    # Dashboard should render in French
    response = client.get("/dashboard")
    assert "Recettes" in response.text


# ── Registration stores request language ──────────────────────────────────────


def test_register_stores_request_language(client, db):
    client.post("/set-language", data={"lang": "fr"})
    client.post("/register", data=VALID_USER)
    user = _get_user(db)
    assert user.language == "fr"
