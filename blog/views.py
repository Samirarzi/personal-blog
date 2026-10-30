from django.http import JsonResponse
from .models import post
from django.core.paginator import InvalidPage, Paginator
from django.shortcuts import get_object_or_404, render

def post_list(request):
    query = request.GET.get("q", "").strip()

    posts = post.objects.filter(is_published=True)

    if query:
        posts = posts.filter(title__icontains=query)

    posts = posts.order_by("-created_at", "-pk")
    paginator = Paginator(posts, 5)

    page_number = request.GET.get("page", "1")

    try:
        page = paginator.page(page_number)
    except InvalidPage:
        return JsonResponse({"error": "Invalid page"}, status=400)

    data = list(
        page.object_list.values("id", "title", "body", "created_at")
    )

    return JsonResponse(
        {
            "posts": data,
            "pagination": {
                "page": page.number,
                "pages": paginator.num_pages,
                "total": paginator.count,
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
            },
        },
        json_dumps_params={"ensure_ascii": False},
    )
def home(request):
    query = request.GET.get("q", "").strip()

    posts = post.objects.filter(is_published=True)

    if query:
        posts = posts.filter(title__icontains=query)

    posts = posts.order_by("-created_at", "-pk")
    paginator = Paginator(posts, 5)
    page = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "blog/home.html",
        {
            "articles": page.object_list,
            "page": page,
            "query": query,
        },
    )


def article_page(request, post_id):
    article = get_object_or_404(
        post,
        pk=post_id,
        is_published=True,
    )

    return render(request, "blog/article_detail.html", {"article": article})
def post_detail(request, post_id):
    try:
        article = post.objects.get(pk=post_id, is_published=True)
    except post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)

    data = {
        "id": article.id,
        "title": article.title,
        "body": article.body,
        "created_at": article.created_at,
    }
    return JsonResponse({"post": data}, json_dumps_params={"ensure_ascii": False})
