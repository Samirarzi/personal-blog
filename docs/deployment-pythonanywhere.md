# Deploying Samir's blog on PythonAnywhere

This guide runs the Django application, admin, and API on a free Beginner
account. Use the account's `USERNAME.pythonanywhere.com` address. Replace
`USERNAME` below with the real account name and use the exact hostname shown
on the Web tab.

Free accounts currently have one web app and 512 MiB of file storage. The web
app needs renewal after one month. A custom registered domain is a separate
purchase and requires a paid PythonAnywhere plan.

## 1. Publish the current project

On the Windows computer, in the project directory:

```cmd
git push -u origin master
```

If GitHub authentication needs refreshing, run
`gh auth login --hostname github.com --git-protocol https --web`, finish the
browser login yourself, and run `gh auth setup-git --hostname github.com`.

## 2. Install the project on the host

The following commands belong in a PythonAnywhere **Bash console**, not Windows CMD.
Use a system image that includes Python 3.13, such as `innit`.

```bash
git clone https://github.com/Samirarzi/personal-blog.git
cd ~/personal-blog
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On the Web tab, add a web app using **Manual configuration** and Python 3.13.
Set its virtualenv path to `/home/USERNAME/personal-blog/.venv`.

## 3. Configure the hosted WSGI application

Generate a production key in the host's Bash console:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Open the WSGI configuration file linked on the **Web tab**. Replace its contents
with the following, filling in the username and generated key. This is the
host's private WSGI file, not the repository's `config/wsgi.py`.

```python
import os
import sys

project_path = "/home/USERNAME/personal-blog"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_production"
os.environ["DJANGO_ALLOWED_HOSTS"] = "USERNAME.pythonanywhere.com"
os.environ["DJANGO_SECRET_KEY"] = "REPLACE_WITH_THE_GENERATED_KEY"
os.environ["BLOG_OWNER_USERNAME"] = "samir"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

Keep the real key in this private host configuration, outside Git. The
production settings require the key and allowed hostname, disable debug
output, require HTTPS, and secure the admin cookies. No proxy-header override
is configured; HTTPS handling must be checked on the actual hosted app.

## 4. Prepare the database and static files

In the host's Bash console, with the virtualenv active, set the same values:

```bash
export DJANGO_SETTINGS_MODULE=config.settings_production
export DJANGO_ALLOWED_HOSTS=USERNAME.pythonanywhere.com
export DJANGO_SECRET_KEY='REPLACE_WITH_THE_SAME_GENERATED_KEY'
export BLOG_OWNER_USERNAME=samir

python manage.py migrate
python manage.py createsuperuser --username samir
python manage.py collectstatic --noinput
```

The generated `staticfiles/` directory is ignored by Git. In the Web tab's
**Static files** section, map `/static/` to
`/home/USERNAME/personal-blog/staticfiles`.

SQLite data is stored in `/home/USERNAME/personal-blog/db.sqlite3`. That file
is also ignored by Git, so the hosted site starts with a fresh database.
Create articles through `/writer/`; local articles can be transferred separately.
Download a backup of the database before later database changes.

## 5. Reload and check the site

Enable **Force HTTPS** on the Web tab and reload the web app. Verify the home
page, search, article links, stylesheet, and owner sign-in at the HTTPS address.
Confirm that drafts stay private.

Run `python manage.py check --deploy` with the production environment active.
HSTS remains disabled during initial setup; enable it only after HTTPS works
correctly. Any other deployment warning should be resolved before considering
the hosted setup complete.

For later code updates, use `git pull` in the host's project directory, install
changed requirements if necessary, run migrations and `collectstatic`, then
reload the web app.

## Official references

- [Free-account features](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)
- [Python versions](https://help.pythonanywhere.com/pages/PythonVersions/)
- [Existing Django project](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)
- [Static files](https://help.pythonanywhere.com/pages/DjangoStaticFiles/)
- [Free web-app renewal](https://blog.pythonanywhere.com/129/)
- [Django deployment settings](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
