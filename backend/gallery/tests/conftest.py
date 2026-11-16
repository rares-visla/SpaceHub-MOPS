"""Fixture-uri comune. API-ul NASA este mereu simulat: testele nu ies in retea."""
import pytest
import responses
from django.core.cache import cache
from rest_framework.test import APIClient

APOD_URL = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
APOD_IMAGE = "https://assets.science.nasa.gov/content/dam/science/cds/apod/2026/11/orion.jpg"
SEARCH_URL = "https://images-api.nasa.gov/search"
ASSET_URL = "https://images-api.nasa.gov/asset"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def nasa():
    """Orice cerere HTTP neinregistrata aici face testul sa pice."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock


def apod_payload(**overrides):
    """O intrare din noul API APOD (science.nasa.gov/wp-json/wp/v2/apod-basic)."""
    payload = {
        "date": "2026-11-15T00:00:00",
        "title": "Nebuloasa Orion &amp; vecinii",
        "explanation": "<p><strong>Explanation:</strong> O regiune de <a href='#'>formare stelara</a>.</p>"
                       "<p>Tomorrow's picture: surpriza</p>",
        "url": "https://science.nasa.gov/image-article/apod-2026-november-15-orion/",
        "hdurl": APOD_IMAGE + "?w=0&h=0&fit=clip",
        "copyright": "<p>Image Credit &amp; Copyright: <a href='#'>Jane Doe</a></p>",
        "basic_html": "<p>...</p>",
    }
    payload.update(overrides)
    return payload


def search_item(nasa_id="PIA00001", title="Mars", date="2015-03-04T00:00:00Z", **data):
    return {
        "href": f"https://images-assets.nasa.gov/image/{nasa_id}/collection.json",
        "data": [
            {
                "nasa_id": nasa_id,
                "title": title,
                "date_created": date,
                "media_type": "image",
                "description": "Descriere completa.",
                "center": "JPL",
                **data,
            }
        ],
        "links": [
            {
                "href": f"http://images-assets.nasa.gov/image/{nasa_id}/{nasa_id}~thumb.jpg",
                "rel": "preview",
                "render": "image",
            }
        ],
    }


def search_payload(items, total=None, has_next=False):
    links = [{"rel": "next", "prompt": "Next", "href": "x"}] if has_next else []
    return {
        "collection": {
            "version": "1.0",
            "items": items,
            "metadata": {"total_hits": len(items) if total is None else total},
            "links": links,
        }
    }


def asset_payload(nasa_id="PIA00001", suffixes=("orig.tif", "large.jpg", "medium.jpg", "thumb.jpg")):
    return {
        "collection": {
            "items": [
                {"href": f"http://images-assets.nasa.gov/image/{nasa_id}/{nasa_id}~{s}"}
                for s in suffixes
            ]
        }
    }
