from django.urls import path

from . import writer_views


urlpatterns = [
    path("sign-in/", writer_views.OwnerLoginView.as_view(), name="writer_login"),
    path("sign-out/", writer_views.writer_logout, name="writer_logout"),
    path("", writer_views.writer_dashboard, name="writer_dashboard"),
    path("new/", writer_views.writer_new, name="writer_new"),
    path("posts/<int:post_id>/edit/", writer_views.writer_edit, name="writer_edit"),
    path(
        "posts/<int:post_id>/preview/", writer_views.writer_preview, name="writer_preview"
    ),
    path("posts/<int:post_id>/status/", writer_views.writer_status, name="writer_status"),
    path("posts/<int:post_id>/delete/", writer_views.writer_delete, name="writer_delete"),
]
