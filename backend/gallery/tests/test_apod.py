"""US01 - Vizualizare APOD (noul API: science.nasa.gov/wp-json/wp/v2/apod-basic)."""
import requests
import responses

from .conftest import APOD_IMAGE, APOD_URL, apod_payload

LOGO = "https://science.nasa.gov/wp-content/themes/nasa-child/assets/images/nasa-logo@2x.png"


def test_apod_returns_title_description_and_image(api, nasa):
    nasa.get(APOD_URL, json=[apod_payload()])

    response = api.get("/api/apod/")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Nebuloasa Orion & vecinii"
    assert body["explanation"] == "O regiune de formare stelara."
    assert body["media_type"] == "image"
    assert body["date"] == "2026-11-15"


def test_apod_asks_for_the_newest_entry(api, nasa):
    nasa.get(APOD_URL, json=[apod_payload()])

    api.get("/api/apod/")

    assert nasa.calls[0].request.params == {"per_page": "1"}


def test_apod_image_comes_from_hdurl_not_from_article_url(api, nasa):
    """In noul API `url` este pagina articolului, iar imaginea este `hdurl`."""
    nasa.get(APOD_URL, json=[apod_payload()])

    body = api.get("/api/apod/").json()

    assert body["hd_image_url"] == APOD_IMAGE
    assert body["image_url"] == APOD_IMAGE + "?w=1280"
    assert "image-article" not in body["image_url"]


def test_apod_strips_html_from_explanation_and_credit(api, nasa):
    nasa.get(APOD_URL, json=[apod_payload()])

    body = api.get("/api/apod/").json()

    assert "<" not in body["explanation"]
    assert "Explanation:" not in body["explanation"]
    assert "Tomorrow" not in body["explanation"]
    assert body["copyright"] == "Jane Doe"


def test_apod_accepts_wordpress_style_rendered_title(api, nasa):
    nasa.get(APOD_URL, json=[apod_payload(title={"rendered": "Titlu <em>redat</em>"})])

    assert api.get("/api/apod/").json()["title"] == "Titlu redat"


def test_apod_never_shows_the_nasa_logo_placeholder(api, nasa):
    """Regresia din 2026: NASA a servit logo-ul site-ului in locul imaginii."""
    nasa.get(APOD_URL, json=[apod_payload(hdurl=LOGO)])

    body = api.get("/api/apod/").json()

    assert body["image_url"] is None
    assert body["hd_image_url"] is None
    assert body["media_type"] == "other"


def test_apod_video_uses_youtube_thumbnail(api, nasa):
    nasa.get(
        APOD_URL,
        json=[
            apod_payload(
                hdurl=None,
                basic_html='<iframe src="https://www.youtube.com/embed/abc123XYZ_-"></iframe>',
            )
        ],
    )

    body = api.get("/api/apod/").json()

    assert body["media_type"] == "video"
    assert body["image_url"] == "https://img.youtube.com/vi/abc123XYZ_-/hqdefault.jpg"
    assert body["video_url"] == "https://www.youtube.com/watch?v=abc123XYZ_-"


def test_apod_without_credit_has_null_copyright(api, nasa):
    payload = apod_payload()
    del payload["copyright"]
    nasa.get(APOD_URL, json=[payload])

    assert api.get("/api/apod/").json()["copyright"] is None


def test_apod_is_cached_between_requests(api, nasa):
    nasa.get(APOD_URL, json=[apod_payload()])

    api.get("/api/apod/")
    api.get("/api/apod/")

    assert len(nasa.calls) == 1


def test_apod_for_specific_date_uses_yymmdd_address(api, nasa):
    nasa.get(f"{APOD_URL}/200102", json=apod_payload(date="2020-01-02T00:00:00"))

    response = api.get("/api/apod/?date=2020-01-02")

    assert response.status_code == 200
    assert response.json()["date"] == "2020-01-02"


def test_apod_unknown_date_returns_404(api, nasa):
    nasa.get(f"{APOD_URL}/200102", status=404)

    assert api.get("/api/apod/?date=2020-01-02").status_code == 404


def test_apod_empty_list_returns_404(api, nasa):
    nasa.get(APOD_URL, json=[])

    assert api.get("/api/apod/").status_code == 404


def test_apod_rejects_malformed_date(api, nasa):
    response = api.get("/api/apod/?date=ieri")

    assert response.status_code == 400
    assert len(nasa.calls) == 0


def test_apod_rejects_date_before_first_apod(api, nasa):
    assert api.get("/api/apod/?date=1990-01-01").status_code == 400


def test_apod_falls_back_to_today_when_entry_has_no_date(api, nasa):
    import datetime as dt

    payload = apod_payload()
    del payload["date"]
    nasa.get(APOD_URL, json=[payload])

    assert api.get("/api/apod/").json()["date"] == dt.date.today().isoformat()


def test_apod_returns_502_when_nasa_fails(api, nasa):
    nasa.get(APOD_URL, status=500)

    response = api.get("/api/apod/")

    assert response.status_code == 502
    assert "detail" in response.json()


def test_apod_returns_502_on_network_error(api, nasa):
    nasa.get(APOD_URL, body=requests.ConnectionError("fara retea"))

    assert api.get("/api/apod/").status_code == 502


def test_apod_returns_502_on_invalid_json(api, nasa):
    nasa.add(responses.GET, APOD_URL, body="<html>oops</html>", status=200)

    assert api.get("/api/apod/").status_code == 502


def test_apod_returns_502_on_unexpected_shape(api, nasa):
    nasa.get(APOD_URL, json="neasteptat")

    assert api.get("/api/apod/").status_code == 502
