"""US16 - Descarcare imagine."""
import pytest
import requests

from gallery import nasa_client
from gallery.nasa_client import NasaApiError

from .conftest import (
    APOD_IMAGE,
    APOD_URL,
    ASSET_URL,
    SEARCH_URL,
    apod_payload,
    asset_payload,
    search_item,
    search_payload,
)

FILE_BYTES = b"\xff\xd8\xff\xe0 continut de imagine"
LARGE_JPG = "https://images-assets.nasa.gov/image/PIA00001/PIA00001~large.jpg"
ORIG_JPG = "https://images-assets.nasa.gov/image/PIA00001/PIA00001~orig.jpg"


def _register_image(nasa, suffixes=("orig.jpg", "large.jpg", "thumb.jpg")):
    nasa.get(SEARCH_URL, json=search_payload([search_item("PIA00001")]))
    nasa.get(f"{ASSET_URL}/PIA00001", json=asset_payload("PIA00001", suffixes=suffixes))


def _body(response):
    return b"".join(response.streaming_content)


def test_download_returns_file_as_attachment(api, nasa):
    _register_image(nasa)
    nasa.get(ORIG_JPG, body=FILE_BYTES, content_type="image/jpeg")

    response = api.get("/api/images/PIA00001/download/")

    assert response.status_code == 200
    assert response["Content-Type"] == "image/jpeg"
    assert response["Content-Disposition"] == 'attachment; filename="PIA00001~orig.jpg"'
    assert _body(response) == FILE_BYTES


def test_download_uses_large_file_when_no_original(api, nasa):
    _register_image(nasa, suffixes=("large.jpg", "thumb.jpg"))
    nasa.get(LARGE_JPG, body=FILE_BYTES, content_type="image/jpeg")

    response = api.get("/api/images/PIA00001/download/")

    assert "PIA00001~large.jpg" in response["Content-Disposition"]
    assert _body(response) == FILE_BYTES


def test_download_unknown_image_returns_404(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([]))

    assert api.get("/api/images/NU-EXISTA/download/").status_code == 404


def test_download_returns_404_when_file_is_gone(api, nasa):
    _register_image(nasa)
    nasa.get(ORIG_JPG, status=404)

    assert api.get("/api/images/PIA00001/download/").status_code == 404


def test_download_returns_502_when_file_server_fails(api, nasa):
    _register_image(nasa)
    nasa.get(ORIG_JPG, status=500)

    assert api.get("/api/images/PIA00001/download/").status_code == 502


def test_download_returns_502_on_network_error(api, nasa):
    _register_image(nasa)
    nasa.get(ORIG_JPG, body=requests.ConnectionError("fara retea"))

    assert api.get("/api/images/PIA00001/download/").status_code == 502


def test_download_returns_404_when_image_has_no_file(api, nasa):
    item = search_item("PIA00001")
    item["links"] = []
    nasa.get(SEARCH_URL, json=search_payload([item]))
    nasa.get(f"{ASSET_URL}/PIA00001", status=404)

    assert api.get("/api/images/PIA00001/download/").status_code == 404


# ------------------------------------------------------------- APOD

def test_apod_download_returns_hd_image(api, nasa):
    nasa.get(APOD_URL, json=[apod_payload()])
    nasa.get(APOD_IMAGE, body=FILE_BYTES, content_type="image/jpeg")

    response = api.get("/api/apod/download/")

    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="orion.jpg"'
    assert _body(response) == FILE_BYTES


def test_apod_download_without_image_returns_404(api, nasa):
    nasa.get(APOD_URL, json=[apod_payload(hdurl=None)])

    assert api.get("/api/apod/download/").status_code == 404


def test_apod_download_refuses_files_outside_nasa(api, nasa):
    """Miniatura unui video APOD sta pe YouTube; nu o descarcam prin server."""
    nasa.get(
        APOD_URL,
        json=[apod_payload(hdurl=None, basic_html="https://www.youtube.com/embed/abc123XYZ")],
    )

    assert api.get("/api/apod/download/").status_code == 502


# ------------------------------------------------------ functii ajutatoare

@pytest.mark.parametrize(
    "url",
    [
        "http://images-assets.nasa.gov/image/a/a~orig.jpg",   # nu e https
        "https://example.com/a.jpg",                            # alta gazda
        "https://images-assets.nasa.gov.evil.com/a.jpg",        # gazda falsa
        "file:///etc/passwd",
        "",
    ],
)
def test_open_image_stream_rejects_untrusted_urls(url, nasa):
    with pytest.raises(NasaApiError):
        nasa_client.open_image_stream(url)
    assert len(nasa.calls) == 0


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://images-assets.nasa.gov/image/a/PIA1~orig.jpg", "PIA1~orig.jpg"),
        ("https://images-assets.nasa.gov/image/a/GSFC%202017%20A~orig.jpg", "GSFC_2017_A~orig.jpg"),
        ("https://apod.nasa.gov/apod/image/x/a%22b%0Ac.jpg", "a_b_c.jpg"),
        ("https://apod.nasa.gov/", "rezerva"),
    ],
)
def test_filename_from_url_is_safe_for_headers(url, expected):
    assert nasa_client.filename_from_url(url, fallback="rezerva") == expected
