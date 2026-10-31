
from django.urls import include, path

from blog import views as blog_views


urlpatterns = [
    path("", blog_views.home, name="home"),
    path("posts/<int:post_id>/", blog_views.article_page, name="article_page"),
    path("writer/", include("blog.writer_urls")),
    path("api/", include("blog.urls")),
]
