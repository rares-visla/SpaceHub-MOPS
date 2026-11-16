"""Client pentru API-urile NASA.

Toate apelurile catre NASA trec prin acest modul, astfel incat:
  * browserul vorbeste doar cu backend-ul nostru;
  * view-urile primesc date deja normalizate;
  * in teste se simuleaza un singur loc (HTTP-ul facut de `requests`).

API-uri folosite (niciunul nu cere cheie):
  * APOD:    https://science.nasa.gov/wp-json/wp/v2/apod-basic
  * Imagini: https://images-api.nasa.gov/search, /asset/{id}

Despre APOD: pe 29 sept. 2026 NASA a mutat APOD de pe apod.nasa.gov pe
science.nasa.gov. Vechiul API (api.nasa.gov/planetary/apod) inca raspunde, dar
intoarce titlul "NASA Science" si logo-ul NASA in loc de imagine, si urmeaza sa
fie arhivat. De aceea citim noul API, care are alta forma:
  * `hdurl` este imaginea, iar `url` este pagina articolului (nu o imagine);
  * `explanation` si creditul contin HTML;
  * o data anume se cere ca /apod-basic/yyMMdd.
"""
from __future__ import annotations

import datetime as dt
import html
import os
import re
from urllib.parse import unquote, urlparse

import requests
from django.conf import settings
from django.core.cache import cache

# Gazdele de pe care avem voie sa descarcam fisiere (vezi `open_image_stream`).
ALLOWED_DOWNLOAD_HOSTS = {
    "images-assets.nasa.gov",
    "assets.science.nasa.gov",
    "apod.nasa.gov",
}
BROWSER_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")

APOD_TODAY_CACHE_SECONDS = 60 * 60          # "azi" se schimba, deci cache scurt
APOD_DATED_CACHE_SECONDS = 60 * 60 * 24     # o data trecuta nu se mai schimba


class NasaApiError(Exception):
    """NASA nu a raspuns sau a raspuns cu o eroare."""


class NasaNotFound(NasaApiError):
    """Resursa ceruta nu exista la NASA."""


# ---------------------------------------------------------------- utilitare

def _get_json(url: str, params: dict | None = None):
    try:
        response = requests.get(
            url, params=params, timeout=settings.NASA_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        raise NasaApiError("Serviciul NASA nu poate fi contactat.") from exc

    if response.status_code == 404:
        raise NasaNotFound("Resursa nu a fost gasita.")
    if response.status_code >= 400:
        raise NasaApiError(f"NASA a raspuns cu status {response.status_code}.")
    try:
        return response.json()
    except ValueError as exc:
        raise NasaApiError("Raspuns invalid de la NASA.") from exc



def _https(url: str | None) -> str | None:
    """NASA intoarce uneori link-uri http://; le servim pe https."""
    if url and url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def _is_browser_image(url: str | None) -> bool:
    return bool(url) and urlparse(url).path.lower().endswith(BROWSER_IMAGE_EXTENSIONS)


# --------------------------------------------------------------------- APOD

APOD_HOME_IMAGE_WIDTH = 1280
_TAG_RE = re.compile(r"<[^>]+>")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_YOUTUBE_RE = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([\w-]{6,})"
)
_EXPLANATION_LABEL_RE = re.compile(r"^\s*explanation\s*:\s*", re.IGNORECASE)
_NEXT_DAY_TEASER_RE = re.compile(r"\s*tomorrow(?:'|\u2019)?s picture\s*:.*$", re.IGNORECASE | re.DOTALL)
_CREDIT_LABEL_RE = re.compile(
    r"^\s*(?:image|video|illustration)?\s*(?:credit|copyright)[^:]{0,40}:\s*",
    re.IGNORECASE,
)


def _text(value) -> str:
    """Text simplu dintr-un camp care poate contine HTML (sau {"rendered": ...})."""
    if isinstance(value, dict):
        value = value.get("rendered", "")
    text = html.unescape(_TAG_RE.sub(" ", str(value or "")))
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r" ([.,;:!?)])", r"\1", text)  # fara spatiu ramas inaintea punctuatiei


def _is_placeholder(url: str | None) -> bool:
    """Logo-ul site-ului NASA, servit uneori in locul imaginii reale."""
    return bool(url) and ("nasa-logo" in url or "/wp-content/themes/" in url)


def _apod_image(raw: dict) -> str | None:
    url = _https(str(raw.get("hdurl") or "").split("?")[0]) or None
    return None if _is_placeholder(url) else url


def _apod_date(raw: dict, requested: str | None) -> str:
    if requested:
        return requested
    candidate = str(raw.get("date") or "")[:10]
    return candidate if _ISO_DATE_RE.match(candidate) else dt.date.today().isoformat()


def get_apod(date: str | None = None) -> dict:
    """Imaginea Astronomica a Zilei (US01). `date` = 'YYYY-MM-DD' sau None (cea mai noua)."""
    cache_key = f"apod:{date or 'today'}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if date:
        slug = dt.date.fromisoformat(date).strftime("%y%m%d")
        raw = _get_json(f"{settings.NASA_APOD_URL}/{slug}")
    else:
        raw = _get_json(settings.NASA_APOD_URL, {"per_page": 1})
    if isinstance(raw, list):  # colectia intoarce o lista, cea mai noua intrare prima
        if not raw:
            raise NasaNotFound("Nu exista APOD pentru aceasta data.")
        raw = raw[0]
    if not isinstance(raw, dict):
        raise NasaApiError("Raspuns invalid de la NASA.")

    image = _apod_image(raw)
    video = _YOUTUBE_RE.search(f"{raw.get('basic_html') or ''} {raw.get('url') or ''}")
    if raw.get("media_type") == "video" or (video and not image):
        media_type = "video"
    else:
        media_type = "image" if image else "other"

    if image:
        image_url = f"{image}?w={APOD_HOME_IMAGE_WIDTH}"  # varianta mai mica pt. prima pagina
    elif video:
        image_url = f"https://img.youtube.com/vi/{video.group(1)}/hqdefault.jpg"
    else:
        image_url = None

    explanation = _text(raw.get("explanation"))
    explanation = _EXPLANATION_LABEL_RE.sub("", explanation)
    explanation = _NEXT_DAY_TEASER_RE.sub("", explanation)
    credit = _CREDIT_LABEL_RE.sub("", _text(raw.get("copyright") or raw.get("credit")))

    apod = {
        "date": _apod_date(raw, date),
        "title": _text(raw.get("title")),
        "explanation": explanation,
        "media_type": media_type,
        "image_url": image_url,
        "hd_image_url": image or image_url,
        "video_url": (
            f"https://www.youtube.com/watch?v={video.group(1)}"
            if media_type == "video" and video
            else None
        ),
        "copyright": credit or None,
    }
    timeout = APOD_DATED_CACHE_SECONDS if date else APOD_TODAY_CACHE_SECONDS
    cache.set(cache_key, apod, timeout)
    return apod


# ------------------------------------------------------------------ cautare

def search_images(
    query: str,
    year_start: int | None = None,
    year_end: int | None = None,
    page: int = 1,
) -> dict:
    """Cautare dupa cuvant cheie (US02), optional filtrata dupa an (US10)."""
    params = {
        "q": query,
        "media_type": "image",
        "page": page,
        "page_size": settings.SEARCH_PAGE_SIZE,
    }
    if year_start is not None:
        params["year_start"] = year_start
    if year_end is not None:
        params["year_end"] = year_end

    collection = _get_json(f"{settings.NASA_IMAGES_URL}/search", params).get(
        "collection", {}
    )
    results = []
    for item in collection.get("items", []):
        data = (item.get("data") or [{}])[0]
        if not data.get("nasa_id"):
            continue
        results.append(
            {
                "nasa_id": data["nasa_id"],
                "title": data.get("title", ""),
                "date_created": data.get("date_created"),
                "thumbnail_url": _preview_link(item),
            }
        )

    total = collection.get("metadata", {}).get("total_hits", len(results))
    has_next = any(
        link.get("rel") == "next" for link in collection.get("links") or []
    )
    return {
        "results": results,
        "total": total,
        "page": page,
        "page_size": settings.SEARCH_PAGE_SIZE,
        "has_next": has_next,
    }


def _preview_link(item: dict) -> str | None:
    links = item.get("links") or []
    for link in links:
        if link.get("rel") == "preview":
            return _https(link.get("href"))
    return _https(links[0].get("href")) if links else None


# ------------------------------------------------------------------ detalii

def get_image(nasa_id: str) -> dict:
    """Detaliile complete ale unei imagini (US03)."""
    collection = _get_json(
        f"{settings.NASA_IMAGES_URL}/search",
        {"nasa_id": nasa_id, "media_type": "image"},
    ).get("collection", {})
    items = collection.get("items") or []
    if not items:
        raise NasaNotFound("Imaginea nu a fost gasita.")

    item = items[0]
    data = (item.get("data") or [{}])[0]
    thumbnail = _preview_link(item)

    try:
        files = _asset_files(nasa_id)
    except NasaNotFound:
        files = []

    display_url = _pick(files, ("~large", "~orig", "~medium", "~small")) or thumbnail
    original = _pick(files, ("~orig",))
    # Originalul poate fi TIFF (nu se afiseaza in browser, dar e bun de descarcat).
    download_url = original or display_url

    return {
        "nasa_id": data.get("nasa_id", nasa_id),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "date_created": data.get("date_created"),
        "photographer": data.get("photographer") or None,
        "secondary_creator": data.get("secondary_creator") or None,
        "center": data.get("center") or None,
        "keywords": data.get("keywords") or [],
        "thumbnail_url": thumbnail,
        "image_url": display_url,
        "download_url": download_url,
    }


def _asset_files(nasa_id: str) -> list[str]:
    collection = _get_json(f"{settings.NASA_IMAGES_URL}/asset/{nasa_id}").get(
        "collection", {}
    )
    return [
        _https(entry["href"])
        for entry in collection.get("items", [])
        if entry.get("href")
    ]


def _pick(files: list[str], markers: tuple[str, ...]) -> str | None:
    """Primul fisier care contine unul dintre marcaje, in ordinea preferintei.

    Pentru afisare se accepta doar formate pe care browserul le poate reda;
    pentru '~orig' singur (descarcare) se accepta orice format.
    """
    only_orig = markers == ("~orig",)
    for marker in markers:
        for href in files:
            if marker in href and (only_orig or _is_browser_image(href)):
                return href
    return None


# --------------------------------------------------------------- descarcare

def filename_from_url(url: str, fallback: str = "spacehub-image") -> str:
    name = os.path.basename(unquote(urlparse(url).path))
    name = re.sub(r"[^A-Za-z0-9._~-]+", "_", name).strip("._")
    return name or fallback


def open_image_stream(url: str):
    """Deschide fisierul de la NASA pentru descarcare (US16).

    Intoarce (iterator_de_bytes, content_type). Se accepta doar adrese https de pe
    gazdele NASA cunoscute, ca endpoint-ul sa nu poata fi folosit drept proxy.
    """
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
        raise NasaApiError("Adresa imaginii nu este permisa.")
    try:
        response = requests.get(
            url, stream=True, timeout=settings.NASA_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        raise NasaApiError("Imaginea nu a putut fi descarcata.") from exc
    if response.status_code == 404:
        raise NasaNotFound("Fisierul imaginii nu a fost gasit.")
    if response.status_code >= 400:
        raise NasaApiError(f"NASA a raspuns cu status {response.status_code}.")
    content_type = response.headers.get("Content-Type", "application/octet-stream")
    return response.iter_content(chunk_size=64 * 1024), content_type
