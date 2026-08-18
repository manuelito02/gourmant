import io

from PIL import Image


def _make_png(width: int = 10, height: int = 10) -> bytes:
    """Return a minimal PNG as bytes."""
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _post_image(client, png_bytes: bytes, filename: str = "test.png"):
    return client.post(
        "/api/uploads",
        files={"file": (filename, io.BytesIO(png_bytes), "image/png")},
    )


# ── Auth ───────────────────────────────────────────────────────────────────────


def test_anon_upload_returns_401(client):
    response = _post_image(client, _make_png())
    assert response.status_code == 401


# ── Happy path ─────────────────────────────────────────────────────────────────


def test_upload_returns_filename_and_urls(auth_client, tmp_uploads_dir):
    response = _post_image(auth_client, _make_png())
    assert response.status_code == 201
    data = response.json()
    assert data["filename"].endswith(".jpg")
    assert data["url"] == f"/uploads/{data['filename']}"
    assert data["thumb_url"] == f"/uploads/thumb_{data['filename']}"


def test_upload_writes_original_and_thumb(auth_client, tmp_uploads_dir):
    import pathlib

    response = _post_image(auth_client, _make_png())
    assert response.status_code == 201
    data = response.json()

    uploads = pathlib.Path(tmp_uploads_dir)
    assert (uploads / data["filename"]).exists()
    assert (uploads / ("thumb_" + data["filename"])).exists()


def test_upload_thumbnail_is_small(auth_client, tmp_uploads_dir):
    """A large image must produce a thumbnail capped at THUMB_PX on the long edge."""
    import pathlib

    large_png = _make_png(800, 600)
    response = _post_image(auth_client, large_png)
    assert response.status_code == 201
    data = response.json()

    thumb_path = pathlib.Path(tmp_uploads_dir) / ("thumb_" + data["filename"])
    with Image.open(thumb_path) as img:
        assert max(img.size) <= 400


# ── Validation ─────────────────────────────────────────────────────────────────


def test_non_image_bytes_returns_400(auth_client):
    response = auth_client.post(
        "/api/uploads",
        files={"file": ("not_an_image.jpg", io.BytesIO(b"this is not image data"), "image/jpeg")},
    )
    assert response.status_code == 400
