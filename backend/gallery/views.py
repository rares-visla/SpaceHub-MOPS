"""Endpoint-urile publice (rol: vizitator)."""
from __future__ import annotations

import datetime as dt
from functools import wraps

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import nasa_client
from .nasa_client import NasaApiError, NasaNotFound

MIN_YEAR = 1900
FIRST_APOD_DATE = dt.date(1995, 6, 16)


class BadRequest(Exception):
    pass


def handle_errors(view):
    """Transforma erorile de validare si pe cele NASA in raspunsuri JSON."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except BadRequest as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except NasaNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NasaApiError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    return wrapper


# ---------------------------------------------------------------- validare

def parse_apod_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        raise BadRequest("Data trebuie sa aiba formatul YYYY-MM-DD.")
    if parsed < FIRST_APOD_DATE or parsed > dt.date.today():
        raise BadRequest("Nu exista APOD pentru aceasta data.")
    return parsed.isoformat()


def parse_year(value: str | None, name: str) -> int | None:
    if value in (None, ""):
        return None
    if not value.isdigit() or len(value) != 4:
        raise BadRequest(f"{name} trebuie sa fie un an din 4 cifre.")
    year = int(value)
    if year < MIN_YEAR or year > dt.date.today().year:
        raise BadRequest(
            f"{name} trebuie sa fie intre {MIN_YEAR} si {dt.date.today().year}."
        )
    return year


def parse_page(value: str | None) -> int:
    if value in (None, ""):
        return 1
    if not value.isdigit() or int(value) < 1:
        raise BadRequest("page trebuie sa fie un numar intreg pozitiv.")
    return int(value)


# -------------------------------------------------------------------- APOD

@api_view(["GET"])
@handle_errors
def apod(request):
    """US01 - GET /api/apod/?date=YYYY-MM-DD (fara `date` = imaginea de azi)."""
    date = parse_apod_date(request.query_params.get("date"))
    return Response(nasa_client.get_apod(date))


@api_view(["GET"])
@handle_errors
def apod_download(request):
    """US16 - GET /api/apod/download/?date=YYYY-MM-DD"""
    date = parse_apod_date(request.query_params.get("date"))
    data = nasa_client.get_apod(date)
    if not data.get("hd_image_url"):
        raise NasaNotFound("Aceasta intrare APOD nu are o imagine de descarcat.")
    return _attachment(data["hd_image_url"], fallback=f"apod-{data.get('date')}")


# ----------------------------------------------------------------- imagini

@api_view(["GET"])
@handle_errors
def image_search(request):
    """US02 + US10 - GET /api/images/search/?q=&year_start=&year_end=&page="""
    query = (request.query_params.get("q") or "").strip()
    if not query:
        raise BadRequest("Introdu un cuvant cheie pentru cautare.")
    year_start = parse_year(request.query_params.get("year_start"), "year_start")
    year_end = parse_year(request.query_params.get("year_end"), "year_end")
    if year_start and year_end and year_start > year_end:
        raise BadRequest("Anul de inceput nu poate fi dupa anul de sfarsit.")
    page = parse_page(request.query_params.get("page"))
    return Response(nasa_client.search_images(query, year_start, year_end, page))


@api_view(["GET"])
@handle_errors
def image_detail(request, nasa_id: str):
    """US03 - GET /api/images/<nasa_id>/"""
    return Response(nasa_client.get_image(nasa_id))


@api_view(["GET"])
@handle_errors
def image_download(request, nasa_id: str):
    """US16 - GET /api/images/<nasa_id>/download/"""
    image = nasa_client.get_image(nasa_id)
    if not image.get("download_url"):
        raise NasaNotFound("Imaginea nu are un fisier de descarcat.")
    return _attachment(image["download_url"], fallback=nasa_id)


def _attachment(url: str, fallback: str) -> StreamingHttpResponse:
    """Trimite fisierul cu `Content-Disposition: attachment`.

    Atributul HTML `download` este ignorat pentru fisiere de pe alt domeniu,
    de aceea descarcarea trece prin backend.
    """
    chunks, content_type = nasa_client.open_image_stream(url)
    filename = nasa_client.filename_from_url(url, fallback=fallback)
    response = StreamingHttpResponse(chunks, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
