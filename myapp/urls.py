from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path(
        "search/",
        views.search_albums,
        name="search_albums"
    ),

    path(
        "edit/<int:album_id>/",
        views.edit_album,
        name="edit_album"
    ),

    path(
        "delete/<int:album_id>/",
        views.delete_album,
        name="delete_album"
    ),
]
