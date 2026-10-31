from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from .access import is_blog_owner, owner_required
from .forms import ArticleForm, OwnerAuthenticationForm
from .models import post


class OwnerLoginView(LoginView):
    template_name = "blog/writer/login.html"
    authentication_form = OwnerAuthenticationForm
    redirect_authenticated_user = True
    next_page = "writer_dashboard"

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not is_blog_owner(request.user):
            return HttpResponseForbidden(
                "This writing area is available only to the blog owner."
            )
        return super().dispatch(request, *args, **kwargs)


writer_logout = owner_required(LogoutView.as_view(next_page="home"))


@owner_required
@require_safe
def writer_dashboard(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")
    if status not in {"all", "draft", "published"}:
        return HttpResponseBadRequest("Invalid article status.")

    counts = post.objects.aggregate(
        total=Count("pk"),
        published=Count("pk", filter=Q(is_published=True)),
        drafts=Count("pk", filter=Q(is_published=False)),
    )
    articles = post.objects.all()
    if query:
        articles = articles.filter(
            Q(title__icontains=query) | Q(body__icontains=query)
        )
    if status == "draft":
        articles = articles.filter(is_published=False)
    elif status == "published":
        articles = articles.filter(is_published=True)

    articles = articles.order_by("-created_at", "-pk")
    page = Paginator(articles, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "blog/writer/dashboard.html",
        {
            "articles": page.object_list,
            "page": page,
            "query": query,
            "status": status,
            "counts": counts,
        },
    )


def _editor(request, article=None):
    is_new = article is None
    action = request.POST.get("action", "save")
    if request.method == "POST" and action not in {"save", "publish"}:
        return HttpResponseBadRequest("Invalid editor action.")

    form = ArticleForm(
        request.POST if request.method == "POST" else None,
        instance=article,
    )
    if request.method == "POST" and form.is_valid():
        saved_article = form.save(commit=False)
        if action == "publish":
            saved_article.is_published = True
        elif is_new:
            saved_article.is_published = False
        saved_article.save()

        if action == "publish":
            messages.success(request, "Article published.")
            return redirect("article_page", post_id=saved_article.pk)
        messages.success(request, "Draft saved." if is_new else "Changes saved.")
        return redirect("writer_edit", post_id=saved_article.pk)

    return render(
        request,
        "blog/writer/editor.html",
        {"form": form, "article": article, "is_new": is_new},
    )


@owner_required
@require_http_methods(["GET", "POST"])
def writer_new(request):
    return _editor(request)


@owner_required
@require_http_methods(["GET", "POST"])
def writer_edit(request, post_id):
    article = get_object_or_404(post, pk=post_id)
    return _editor(request, article)


@owner_required
@require_safe
def writer_preview(request, post_id):
    article = get_object_or_404(post, pk=post_id)
    return render(
        request,
        "blog/article_detail.html",
        {"article": article, "preview": True},
    )


@owner_required
@require_POST
def writer_status(request, post_id):
    action = request.POST.get("action")
    if action not in {"publish", "unpublish"}:
        return HttpResponseBadRequest("Invalid publication action.")

    article = get_object_or_404(post, pk=post_id)
    if action == "publish":
        form = ArticleForm({"title": article.title, "body": article.body})
        if not form.is_valid():
            return HttpResponseBadRequest(
                "Add a valid title and article body before publishing."
            )
    article.is_published = action == "publish"
    article.save(update_fields=["is_published"])
    messages.success(
        request,
        "Article published." if article.is_published else "Article moved to drafts.",
    )
    return redirect("writer_dashboard")


@owner_required
@require_http_methods(["GET", "POST"])
def writer_delete(request, post_id):
    article = get_object_or_404(post, pk=post_id)
    if request.method == "POST":
        article.delete()
        messages.success(request, "Article deleted.")
        return redirect("writer_dashboard")
    return render(request, "blog/writer/delete.html", {"article": article})
