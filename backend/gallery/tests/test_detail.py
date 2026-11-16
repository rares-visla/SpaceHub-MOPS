"""US03 - Detalii imagine; US15 - link-ul public al paginii de detalii."""
from .conftest import ASSET_URL, SEARCH_URL, asset_payload, search_item, search_payload


def _register(nasa, nasa_id="PIA00001", suffixes=None, **data):
    nasa.get(SEARCH_URL, json=search_payload([search_item(nasa_id, **data)]))
    kwargs = {"suffixes": suffixes} if suffixes else {}
    nasa.get(f"{ASSET_URL}/{nasa_id}", json=asset_payload(nasa_id, **kwargs))


def test_detail_returns_full_information(api, nasa):
    _register(nasa, photographer="NASA/Bill Ingalls", keywords=["Mars", "Rover"])

    response = api.get("/api/images/PIA00001/")

    assert response.status_code == 200
    body = response.json()
    assert body["nasa_id"] == "PIA00001"
    assert body["title"] == "Mars"
    assert body["description"] == "Descriere completa."
    assert body["date_created"] == "2015-03-04T00:00:00Z"
    assert body["photographer"] == "NASA/Bill Ingalls"
    assert body["center"] == "JPL"
    assert body["keywords"] == ["Mars", "Rover"]


def test_detail_looks_up_the_exact_nasa_id(api, nasa):
    _register(nasa)

    api.get("/api/images/PIA00001/")

    assert nasa.calls[0].request.params["nasa_id"] == "PIA00001"


def test_detail_uses_large_rendition_for_display(api, nasa):
    _register(nasa)

    body = api.get("/api/images/PIA00001/").json()

    assert body["image_url"] == "https://images-assets.nasa.gov/image/PIA00001/PIA00001~large.jpg"


def test_detail_offers_original_file_for_download_even_if_tiff(api, nasa):
    _register(nasa)

    body = api.get("/api/images/PIA00001/").json()

    assert body["download_url"].endswith("PIA00001~orig.tif")


def test_detail_uses_original_for_display_when_no_large_exists(api, nasa):
    _register(nasa, suffixes=("orig.jpg", "thumb.jpg"))

    body = api.get("/api/images/PIA00001/").json()

    assert body["image_url"].endswith("PIA00001~orig.jpg")


def test_detail_falls_back_to_thumbnail_when_asset_manifest_is_missing(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([search_item("PIA00001")]))
    nasa.get(f"{ASSET_URL}/PIA00001", status=404)

    response = api.get("/api/images/PIA00001/")

    assert response.status_code == 200
    assert response.json()["image_url"].endswith("PIA00001~thumb.jpg")


def test_detail_missing_photographer_is_null(api, nasa):
    _register(nasa)

    assert api.get("/api/images/PIA00001/").json()["photographer"] is None


def test_detail_unknown_image_returns_404(api, nasa):
    nasa.get(SEARCH_URL, json=search_payload([]))

    response = api.get("/api/images/NU-EXISTA/")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_detail_returns_502_when_nasa_fails(api, nasa):
    nasa.get(SEARCH_URL, status=500)

    assert api.get("/api/images/PIA00001/").status_code == 502


def test_detail_supports_ids_with_spaces(api, nasa):
    _register(nasa, nasa_id="GSFC 2017 A")

    response = api.get("/api/images/GSFC%202017%20A/")

    assert response.status_code == 200
    assert nasa.calls[0].request.params["nasa_id"] == "GSFC 2017 A"


def test_detail_is_public_without_account(api, nasa):
    """US15: oricine deschide link-ul vede detaliile, fara cont."""
    _register(nasa)

    response = api.get("/api/images/PIA00001/")  # fara nicio autentificare

    assert response.status_code == 200
