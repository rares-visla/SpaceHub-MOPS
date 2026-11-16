"""US02 - Cautare imagini; US10 - Filtrare dupa an."""
import datetime as dt

from .conftest import SEARCH_URL, search_item, search_payload


# ------------------------------------------------------------------- US02

def test_search_returns_grid_items(api, nasa):
    nasa.get(
        SEARCH_URL,
        json=search_payload(
            [search_item("PIA1", "Mars la apus"), search_item("PIA2", "Olympus Mons")],
            total=336,
            has_next=True,
        ),
    )

    response = api.get("/api/images/search/?q=Mars")

    assert response.status_code == 200
    body = response.json()
    assert [r["nasa_id"] for r in body["results"]] == ["PIA1", "PIA2"]
    assert body["results"][0]["title"] == "Mars la apus"
    assert body["total"] == 336
    assert body["has_next"] is True
    assert body["page"] == 1


def test_search_thumbnails_are_served_over_https(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([search_item("PIA1")]))

    thumb = api.get("/api/images/search/?q=Mars").json()["results"][0]["thumbnail_url"]

    assert thumb == "https://images-assets.nasa.gov/image/PIA1/PIA1~thumb.jpg"


def test_search_asks_nasa_only_for_images(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([]))

    api.get("/api/images/search/?q=Mars")

    params = nasa.calls[0].request.params
    assert params["q"] == "Mars"
    assert params["media_type"] == "image"


def test_search_with_no_results_returns_empty_list(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([]))

    body = api.get("/api/images/search/?q=zzzzqqq").json()

    assert body["results"] == []
    assert body["total"] == 0
    assert body["has_next"] is False


def test_search_requires_keyword(api, nasa):
    for url in ("/api/images/search/", "/api/images/search/?q=", "/api/images/search/?q=%20%20"):
        assert api.get(url).status_code == 400
    assert len(nasa.calls) == 0


def test_search_passes_page_to_nasa(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([search_item()]))

    body = api.get("/api/images/search/?q=Mars&page=3").json()

    assert nasa.calls[0].request.params["page"] == "3"
    assert body["page"] == 3


def test_search_rejects_invalid_page(api, nasa):
    assert api.get("/api/images/search/?q=Mars&page=0").status_code == 400
    assert api.get("/api/images/search/?q=Mars&page=abc").status_code == 400


def test_search_skips_items_without_nasa_id(api, nasa):
    broken = {"data": [{"title": "fara id"}], "links": []}
    nasa.get(SEARCH_URL, json=search_payload([broken, search_item("PIA9")]))

    results = api.get("/api/images/search/?q=Mars").json()["results"]

    assert [r["nasa_id"] for r in results] == ["PIA9"]


def test_search_returns_502_when_nasa_fails(api, nasa):
    nasa.get(SEARCH_URL, status=503)

    assert api.get("/api/images/search/?q=Mars").status_code == 502


# ------------------------------------------------------------------- US10

def test_year_filters_are_sent_to_nasa(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([search_item()]))

    response = api.get("/api/images/search/?q=Mars&year_start=2010&year_end=2015")

    assert response.status_code == 200
    params = nasa.calls[0].request.params
    assert params["year_start"] == "2010"
    assert params["year_end"] == "2015"


def test_year_filters_are_optional(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([search_item()]))

    api.get("/api/images/search/?q=Mars")

    params = nasa.calls[0].request.params
    assert "year_start" not in params
    assert "year_end" not in params


def test_only_start_year_can_be_given(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([search_item()]))

    api.get("/api/images/search/?q=Mars&year_start=2018&year_end=")

    params = nasa.calls[0].request.params
    assert params["year_start"] == "2018"
    assert "year_end" not in params


def test_same_start_and_end_year_is_allowed(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([search_item()]))

    assert api.get("/api/images/search/?q=Mars&year_start=2012&year_end=2012").status_code == 200


def test_start_year_after_end_year_is_rejected(api, nasa):
    response = api.get("/api/images/search/?q=Mars&year_start=2020&year_end=2010")

    assert response.status_code == 400
    assert len(nasa.calls) == 0


def test_non_numeric_year_is_rejected(api, nasa):
    assert api.get("/api/images/search/?q=Mars&year_start=abcd").status_code == 400
    assert api.get("/api/images/search/?q=Mars&year_end=20").status_code == 400
    assert api.get("/api/images/search/?q=Mars&year_start=-200").status_code == 400


def test_year_out_of_range_is_rejected(api, nasa):
    next_year = dt.date.today().year + 1

    assert api.get("/api/images/search/?q=Mars&year_start=1800").status_code == 400
    assert api.get(f"/api/images/search/?q=Mars&year_end={next_year}").status_code == 400
