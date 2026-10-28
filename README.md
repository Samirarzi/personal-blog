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
