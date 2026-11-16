from django.urls import path

from . import views

urlpatterns = [
    path("apod/", views.apod, name="apod"),
    path("apod/download/", views.apod_download, name="apod-download"),
    path("images/search/", views.image_search, name="image-search"),
    path("images/<str:nasa_id>/", views.image_detail, name="image-detail"),
    path(
        "images/<str:nasa_id>/download/",
        views.image_download,
        name="image-download",
    ),
]
