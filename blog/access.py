from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache


def is_blog_owner(user):
    owner_username = getattr(settings, "BLOG_OWNER_USERNAME", "")
    return bool(
        owner_username
        and user.is_authenticated
        and user.is_active
        and user.get_username() == owner_username
    )


def owner_required(view):
    @wraps(view)
    def check_owner(request, *args, **kwargs):
        if not is_blog_owner(request.user):
            return HttpResponseForbidden(
                "This writing area is available only to the blog owner."
            )
        return view(request, *args, **kwargs)

    protected_view = login_required(check_owner, login_url="writer_login")
    return never_cache(protected_view)
