from .access import is_blog_owner


def owner_access(request):
    return {"is_blog_owner": is_blog_owner(request.user)}
