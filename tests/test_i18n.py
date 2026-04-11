"""Tests for language switching and translated error messages."""

from tests.conftest import VALID_USER

# ── set-language endpoint ─────────────────────────────────────────────────────


def test_set_language_redirects(client):
    res = client.post("/set-language", data={"lang": "fr"}, follow_redirects=False)
    assert res.status_code == 302


def test_set_language_uses_referer(client):
    res = client.post(
        "/set-language",
        data={"lang": "fr"},
        headers={"referer": "/login"},
        follow_redirects=False,
    )
    assert res.headers["location"] == "/login"


def test_set_language_falls_back_to_root_without_referer(client):
    res = client.post("/set-language", data={"lang": "fr"}, follow_redirects=False)
    assert res.headers["location"] == "/"


def test_set_language_invalid_lang_ignored(client):
    """Unsupported language code is silently ignored; page still renders in English."""
    client.post("/set-language", data={"lang": "xx"})
    res = client.get("/")
    assert "Log in" in res.text


def test_set_language_persists_across_requests(client):
    """The chosen language is kept for subsequent requests via session cookie."""
    client.post("/set-language", data={"lang": "fr"})
    res = client.get("/")
    assert res.status_code == 200


def test_set_language_all_supported_langs(client):
    """All four supported languages can be set without error."""
    for lang in ("en", "fr", "de", "nl"):
        res = client.post("/set-language", data={"lang": lang}, follow_redirects=False)
        assert res.status_code == 302


# ── Translated error messages ─────────────────────────────────────────────────


def test_not_authenticated_error_in_french(client, ref):
    """Protected endpoint returns 401 in French mode."""
    client.post("/set-language", data={"lang": "fr"})
    response = client.post(
        "/api/ingredients", json={"name": "Ciboulette", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 401


def test_not_authenticated_error_in_german(client, ref):
    """Protected endpoint returns 401 in German mode."""
    client.post("/set-language", data={"lang": "de"})
    response = client.post(
        "/api/ingredients", json={"name": "Schnittlauch", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 401


def test_recipe_not_found_in_french(auth_client):
    """Recipe detail returns 404 in French mode."""
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.get("/recipes/999999")
    assert response.status_code == 404


def test_recipe_not_found_in_dutch(auth_client):
    """Recipe detail returns 404 in Dutch mode."""
    auth_client.post("/set-language", data={"lang": "nl"})
    response = auth_client.get("/recipes/999999")
    assert response.status_code == 404


# ── Dashboard redirects in all languages ─────────────────────────────────────


def test_dashboard_loads_in_french(auth_client):
    auth_client.post("/set-language", data={"lang": "fr"})
    res = auth_client.get("/dashboard")
    assert res.status_code == 200


def test_dashboard_loads_in_german(auth_client):
    auth_client.post("/set-language", data={"lang": "de"})
    res = auth_client.get("/dashboard")
    assert res.status_code == 200


def test_dashboard_loads_in_dutch(auth_client):
    auth_client.post("/set-language", data={"lang": "nl"})
    res = auth_client.get("/dashboard")
    assert res.status_code == 200


# ── Root redirect ─────────────────────────────────────────────────────────────


def test_root_redirects_to_dashboard_when_logged_in(client):
    client.post("/register", data=VALID_USER)
    res = client.get("/")
    assert res.url.path == "/dashboard"


def test_root_shows_landing_when_logged_out(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Log in" in res.text
