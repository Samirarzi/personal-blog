# Personal Tech Blog

A personal blog about technology, Python and DevOps.

## Learning goals
- Backend development with Django
- Python programming
- Git, Docker and CI/CD

## Local setup on Windows CMD

    python -m venv .venv
    .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

## Blog API
- GET /api/posts/ - Published articles, 5 per page.
- GET /api/posts/?q=python - Search article titles.
- GET /api/posts/?page=2 - Select a page.
- GET /api/posts/ID/ - Published article details.
- Invalid page: 400. Missing or draft article: 404.

## Tests
    python manage.py test blog

## Website
- `/` - Samir's introduction, article title search, and pagination.
- `/posts/ID/` - Full text of a published article.
- `/admin/` - Create, edit, and publish articles.

The interface is English. Draft articles are hidden from public pages and the API.

## Theme
The dark theme uses orange accents. Change `--accent` and `--accent-hover`
in `blog/static/blog/style.css` to update links, buttons, and keyboard focus.
