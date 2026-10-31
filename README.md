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
- `/writer/` - Samir's private writing desk.
- `/writer/new/` - Write an article and save a draft or publish it.
- `/writer/sign-in/` - Owner sign-in with the existing blog account.

The interface is English. Draft articles are hidden from public pages and the API.

## Writing articles
Sign in at `/writer/sign-in/` with the existing `samir` account and password.
The writing desk supports drafts, editing, private previews, publishing,
unpublishing, and a separate deletion confirmation. There is no public sign-up.

Only the active account named by `BLOG_OWNER_USERNAME` can use the writing desk.
The setting defaults to `samir` and can be set through the environment. Being a
staff member or superuser alone does not grant access to this writing interface.
The old Django admin URL is disabled; article management uses the writing desk.

The editor includes a live plain-text preview, word count, estimated reading
time, and an unsaved-changes reminder. Article text is displayed as text, with
its line breaks preserved. The site also includes a light/dark theme toggle.

## Theme
The dark theme uses orange accents. Change `--accent` and `--accent-hover`
in `blog/static/blog/style.css` to update links, buttons, and keyboard focus.

## Hosting
The local project uses `config.settings`. The hosted HTTPS version uses
`config.settings_production`, with `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`
provided by the hosting environment. This project does not load `.env` automatically.

See [the PythonAnywhere deployment guide](docs/deployment-pythonanywhere.md)
for the free-account setup, static files, and hosted database.
