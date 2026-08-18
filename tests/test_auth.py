from fastapi.testclient import TestClient

from tests.conftest import VALID_USER


def register(client: TestClient, data: dict = VALID_USER) -> None:
    client.post("/register", data=data)
    client.post("/logout")


# ── Pages ─────────────────────────────────────────────────────────────────────


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Log in" in response.text


def test_register_page(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert "Create account" in response.text


def test_login_page_redirects_when_logged_in(client):
    client.post("/register", data=VALID_USER)
    response = client.get("/login")
    assert response.url.path == "/dashboard"


def test_register_page_redirects_when_logged_in(client):
    client.post("/register", data=VALID_USER)
    response = client.get("/register")
    assert response.url.path == "/dashboard"


# ── Health ────────────────────────────────────────────────────────────────────


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Registration ──────────────────────────────────────────────────────────────


def test_register_success(client):
    response = client.post("/register", data=VALID_USER)
    assert response.status_code == 200
    assert "Jane" in response.text


def test_register_duplicate_email(client):
    register(client)
    response = client.post("/register", data=VALID_USER)
    assert response.status_code == 400
    assert "already exists" in response.text


def test_register_password_mismatch(client):
    response = client.post("/register", data={**VALID_USER, "password_confirm": "something-else"})
    assert response.status_code == 400
    assert "do not match" in response.text


def test_register_weak_password(client):
    weak = {**VALID_USER, "password": "password123", "password_confirm": "password123"}
    response = client.post("/register", data=weak)
    assert response.status_code == 400


# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_success(client):
    register(client)
    response = client.post(
        "/login", data={"email": VALID_USER["email"], "password": VALID_USER["password"]}
    )
    assert response.status_code == 200
    assert "Jane" in response.text


def test_login_wrong_password(client):
    register(client)
    response = client.post(
        "/login", data={"email": VALID_USER["email"], "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert "Invalid" in response.text


def test_login_unknown_email(client):
    response = client.post(
        "/login", data={"email": "nobody@example.com", "password": "some-password"}
    )
    assert response.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────


def test_logout_clears_session(client):
    client.post("/register", data=VALID_USER)
    response = client.post("/logout")
    assert response.status_code == 200
    assert "Log in" in response.text


# ── Nav state ─────────────────────────────────────────────────────────────────


def test_nav_shows_login_when_logged_out(client):
    response = client.get("/")
    assert "Log in" in response.text


def test_nav_shows_name_when_logged_in(client):
    client.post("/register", data=VALID_USER)
    response = client.get("/")
    assert "Jane" in response.text


def test_nav_hides_login_after_register(client):
    client.post("/register", data=VALID_USER)
    response = client.get("/")
    assert "Log in" not in response.text
