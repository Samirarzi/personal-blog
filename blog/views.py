from django.http import JsonResponse
from .models import post


def post_list(request):
    posts = post.objects.filter(is_published=True).order_by("-created_at")
    data = list(posts.values("id", "title", "body", "created_at"))
    return JsonResponse({"posts": data}, json_dumps_params={"ensure_ascii": False})
