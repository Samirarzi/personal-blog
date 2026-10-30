from django.http import JsonResponse
from .models import post


def post_list(request):
    posts = post.objects.filter(is_published=True).order_by("-created_at")
    data = list(posts.values("id", "title", "body", "created_at"))
    return JsonResponse({"posts": data}, json_dumps_params={"ensure_ascii": False})


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
