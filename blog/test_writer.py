"""Behavior tests for the private writer area.

These tests use Django's isolated test database. The accounts and passwords
below are test fixtures, not changes to the site's real author account.
"""

from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from blog.models import post


@override_settings(
    BLOG_OWNER_USERNAME="test-owner",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class WriterAreaTests(TestCase):
    owner_password = "test-owner-password-937!"
    other_password = "test-other-password-582!"

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_user(
            username="test-owner", password=cls.owner_password
        )
        cls.other = users.objects.create_user(
            username="another-reader", password=cls.other_password
        )
        cls.staff = users.objects.create_user(
            username="another-staff", password=cls.other_password, is_staff=True
        )
        cls.superuser = users.objects.create_superuser(
            username="another-superuser",
            email="superuser@example.test",
            password=cls.other_password,
        )
        cls.draft = post.objects.create(
            title="Owner draft",
            body="Preview line\n<script>private-marker</script>",
            is_published=False,
        )
        cls.published = post.objects.create(
            title="Public article",
            body="Public article content.",
            is_published=True,
        )

    def writer_url(self, name, article=None):
        if article is None:
            return reverse(name)
        return reverse(name, args=[article.pk])

    def article_snapshot(self):
        return list(
            post.objects.order_by("pk").values_list(
                "pk", "title", "body", "is_published"
            )
        )

    def read_routes(self):
        return [
            self.writer_url("writer_dashboard"),
            self.writer_url("writer_new"),
            self.writer_url("writer_edit", self.draft),
            self.writer_url("writer_preview", self.draft),
            self.writer_url("writer_delete", self.draft),
        ]

    def mutation_routes(self):
        editor_data = {
            "title": "Unauthorized replacement",
            "body": "This must not be saved.",
            "action": "save",
        }
        return [
            (self.writer_url("writer_new"), editor_data),
            (self.writer_url("writer_edit", self.draft), editor_data),
            (
                self.writer_url("writer_status", self.draft),
                {"action": "publish"},
            ),
            (
                self.writer_url("writer_status", self.published),
                {"action": "unpublish"},
            ),
            (self.writer_url("writer_delete", self.draft), {}),
            (self.writer_url("writer_logout"), {}),
        ]

    def assert_login_redirect(self, response, requested_url):
        self.assertEqual(response.status_code, 302)
        destination = urlsplit(response["Location"])
        self.assertEqual(destination.path, reverse("writer_login"))
        self.assertEqual(
            parse_qs(destination.query).get("next"), [requested_url]
        )

    def assert_private_cache_policy(self, response):
        cache_control = response.get("Cache-Control", "").lower()
        self.assertIn("no-store", cache_control)
        self.assertIn("private", cache_control)

    def test_legacy_admin_cannot_bypass_owner_only_authoring(self):
        for user in (self.owner, self.staff, self.superuser):
            self.client.force_login(user)
            for url in ("/admin/", "/admin/blog/post/add/"):
                with self.subTest(username=user.username, url=url):
                    self.assertEqual(self.client.get(url).status_code, 404)

    def test_anonymous_read_routes_redirect_to_owner_sign_in(self):
        for url in self.read_routes():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assert_login_redirect(response, url)

    def test_anonymous_mutations_redirect_and_do_not_change_articles(self):
        before = self.article_snapshot()
        for url, data in self.mutation_routes():
            with self.subTest(url=url, action=data.get("action")):
                response = self.client.post(url, data)
                self.assert_login_redirect(response, url)
                self.assertEqual(self.article_snapshot(), before)

    def test_other_accounts_cannot_read_or_mutate_the_writer_area(self):
        before = self.article_snapshot()
        for user in (self.other, self.staff, self.superuser):
            client = Client()
            client.force_login(user)
            for url in self.read_routes() + [reverse("writer_login")]:
                with self.subTest(user=user.username, method="GET", url=url):
                    self.assertEqual(client.get(url).status_code, 403)
            for url, data in self.mutation_routes():
                with self.subTest(user=user.username, method="POST", url=url):
                    self.assertEqual(client.post(url, data).status_code, 403)
                    self.assertEqual(self.article_snapshot(), before)

    def test_only_owner_credentials_can_sign_in_without_creating_accounts(self):
        before_count = get_user_model().objects.count()
        accounts = (
            (self.owner, self.owner_password, True),
            (self.other, self.other_password, False),
            (self.staff, self.other_password, False),
            (self.superuser, self.other_password, False),
        )
        for user, password, permitted in accounts:
            client = Client()
            with self.subTest(user=user.username):
                response = client.post(
                    reverse("writer_login"),
                    {"username": user.username, "password": password},
                )
                if permitted:
                    self.assertRedirects(
                        response,
                        reverse("writer_dashboard"),
                        fetch_redirect_response=False,
                    )
                    self.assertEqual(client.session[SESSION_KEY], str(user.pk))
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertNotIn(SESSION_KEY, client.session)
        self.assertEqual(get_user_model().objects.count(), before_count)

    def test_wrong_password_and_inactive_owner_cannot_sign_in(self):
        response = self.client.post(
            reverse("writer_login"),
            {"username": self.owner.username, "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)

        self.owner.is_active = False
        self.owner.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("writer_login"),
            {
                "username": self.owner.username,
                "password": self.owner_password,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_owner_configuration_is_exact_and_fails_closed_when_blank(self):
        self.client.force_login(self.owner)
        for configured_name in ("TEST-OWNER", ""):
            with self.subTest(configured_name=configured_name):
                with override_settings(BLOG_OWNER_USERNAME=configured_name):
                    response = self.client.get(reverse("writer_dashboard"))
                    self.assertEqual(response.status_code, 403)

    def test_login_next_keeps_local_destinations_and_rejects_external_ones(self):
        local_destination = self.writer_url("writer_edit", self.draft)
        cases = (
            (local_destination, local_destination),
            ("https://attacker.example/landing", reverse("writer_dashboard")),
            ("//attacker.example/landing", reverse("writer_dashboard")),
        )
        for requested_next, expected_destination in cases:
            with self.subTest(next=requested_next):
                client = Client()
                response = client.post(
                    reverse("writer_login"),
                    {
                        "username": self.owner.username,
                        "password": self.owner_password,
                        "next": requested_next,
                    },
                )
                self.assertRedirects(
                    response,
                    expected_destination,
                    fetch_redirect_response=False,
                )

    def test_saving_new_article_creates_a_private_draft(self):
        self.client.force_login(self.owner)
        before_count = post.objects.count()
        body = "  First paragraph.\nSecond paragraph.  "
        response = self.client.post(
            reverse("writer_new"),
            {
                "title": "New private article",
                "body": body,
                "action": "save",
                "is_published": "on",
            },
        )

        self.assertEqual(post.objects.count(), before_count + 1)
        article = post.objects.get(title="New private article")
        self.assertFalse(article.is_published)
        self.assertEqual(article.body, body)
        self.assertRedirects(
            response,
            self.writer_url("writer_edit", article),
            fetch_redirect_response=False,
        )
        public_client = Client()
        self.assertEqual(
            public_client.get(reverse("article_page", args=[article.pk])).status_code,
            404,
        )
        self.assertEqual(
            public_client.get(reverse("blog:post_detail", args=[article.pk])).status_code,
            404,
        )

    def test_saving_existing_articles_preserves_their_publication_status(self):
        self.client.force_login(self.owner)
        for article in (self.draft, self.published):
            original_status = article.is_published
            body = f"Edited body for article {article.pk}."
            with self.subTest(article=article.pk, published=original_status):
                response = self.client.post(
                    self.writer_url("writer_edit", article),
                    {
                        "title": f"Edited article {article.pk}",
                        "body": body,
                        "action": "save",
                        "is_published": "" if original_status else "on",
                    },
                )
                article.refresh_from_db()
                self.assertEqual(article.is_published, original_status)
                self.assertEqual(article.body, body)
                self.assertRedirects(
                    response,
                    self.writer_url("writer_edit", article),
                    fetch_redirect_response=False,
                )

    def test_valid_editor_publish_works_for_new_and_existing_articles(self):
        self.client.force_login(self.owner)
        cases = (
            (reverse("writer_new"), "Newly published article", None),
            (
                self.writer_url("writer_edit", self.draft),
                "Published former draft",
                self.draft,
            ),
        )
        for url, title, existing_article in cases:
            with self.subTest(url=url):
                response = self.client.post(
                    url,
                    {
                        "title": title,
                        "body": "An article ready for readers.",
                        "action": "publish",
                    },
                )
                article = post.objects.get(title=title)
                if existing_article is not None:
                    self.assertEqual(article.pk, existing_article.pk)
                self.assertTrue(article.is_published)
                self.assertRedirects(
                    response,
                    reverse("article_page", args=[article.pk]),
                    fetch_redirect_response=False,
                )
                self.assertEqual(
                    Client().get(reverse("blog:post_detail", args=[article.pk])).status_code,
                    200,
                )

    def test_publication_actions_change_public_html_and_api_visibility(self):
        self.client.force_login(self.owner)
        status_url = self.writer_url("writer_status", self.draft)
        public_html = reverse("article_page", args=[self.draft.pk])
        public_api = reverse("blog:post_detail", args=[self.draft.pk])
        public_client = Client()

        for action, expected_status, public_status in (
            ("publish", True, 200),
            ("unpublish", False, 404),
        ):
            with self.subTest(action=action):
                response = self.client.post(status_url, {"action": action})
                self.assertRedirects(
                    response,
                    reverse("writer_dashboard"),
                    fetch_redirect_response=False,
                )
                self.draft.refresh_from_db()
                self.assertEqual(self.draft.is_published, expected_status)
                self.assertEqual(public_client.get(public_html).status_code, public_status)
                self.assertEqual(public_client.get(public_api).status_code, public_status)
                listed_ids = [
                    article["id"]
                    for article in public_client.get(reverse("blog:post_list")).json()["posts"]
                ]
                self.assertEqual(self.draft.pk in listed_ids, expected_status)

    def test_invalid_editor_forms_and_actions_do_not_change_the_database(self):
        self.client.force_login(self.owner)
        before = self.article_snapshot()
        routes = (
            reverse("writer_new"),
            self.writer_url("writer_edit", self.draft),
            self.writer_url("writer_edit", self.published),
        )
        cases = (
            ({"title": "", "body": "Body", "action": "publish"}, 200),
            ({"title": "x" * 201, "body": "Body", "action": "publish"}, 200),
            ({"title": "Title", "body": "", "action": "publish"}, 200),
            ({"title": "Title", "body": " \n\t ", "action": "save"}, 200),
            ({"title": "Title", "body": "Body", "action": "destroy"}, 400),
        )
        for url in routes:
            for payload, expected_status in cases:
                with self.subTest(url=url, payload=payload):
                    response = self.client.post(url, payload)
                    self.assertEqual(response.status_code, expected_status)
                    if expected_status == 200:
                        self.assertTrue(response.context["form"].is_bound)
                        self.assertTrue(response.context["form"].errors)
                    self.assertEqual(self.article_snapshot(), before)

    def test_invalid_publication_actions_leave_articles_unchanged(self):
        self.client.force_login(self.owner)
        before = self.article_snapshot()
        for action in (None, "", "save", "delete"):
            payload = {} if action is None else {"action": action}
            with self.subTest(action=action):
                response = self.client.post(
                    self.writer_url("writer_status", self.draft), payload
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.article_snapshot(), before)

    def test_invalid_stored_article_cannot_be_published_by_status_action(self):
        self.client.force_login(self.owner)
        post.objects.filter(pk=self.draft.pk).update(body=" \n\t ")
        before = self.article_snapshot()

        response = self.client.post(
            self.writer_url("writer_status", self.draft), {"action": "publish"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.article_snapshot(), before)

    def test_get_requests_do_not_publish_delete_or_log_out(self):
        self.client.force_login(self.owner)
        before = self.article_snapshot()
        cases = (
            (self.writer_url("writer_status", self.draft), {"action": "publish"}, 405),
            (self.writer_url("writer_status", self.published), {"action": "unpublish"}, 405),
            (reverse("writer_logout"), {}, 405),
            (self.writer_url("writer_delete", self.draft), {"action": "delete"}, 200),
            (reverse("writer_new"), {"action": "publish", "title": "GET draft"}, 200),
            (self.writer_url("writer_edit", self.draft), {"action": "publish"}, 200),
        )
        for url, parameters, expected_status in cases:
            with self.subTest(url=url):
                response = self.client.get(url, parameters)
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(self.article_snapshot(), before)
                self.assertEqual(self.client.session[SESSION_KEY], str(self.owner.pk))

    def test_delete_confirmation_is_read_only_and_post_deletes_the_article(self):
        self.client.force_login(self.owner)
        article_pk = self.published.pk
        delete_url = self.writer_url("writer_delete", self.published)

        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["article"].pk, article_pk)
        self.assertTrue(post.objects.filter(pk=article_pk).exists())

        response = self.client.post(delete_url)
        self.assertRedirects(
            response,
            reverse("writer_dashboard"),
            fetch_redirect_response=False,
        )
        self.assertFalse(post.objects.filter(pk=article_pk).exists())
        public_client = Client()
        self.assertEqual(
            public_client.get(reverse("article_page", args=[article_pk])).status_code,
            404,
        )
        self.assertEqual(
            public_client.get(reverse("blog:post_detail", args=[article_pk])).status_code,
            404,
        )

    def test_owner_can_preview_escaped_draft_without_publishing_it(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.writer_url("writer_preview", self.draft))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["article"].pk, self.draft.pk)
        self.assertTrue(response.context["preview"])
        self.assertContains(response, escape(self.draft.title))
        self.assertContains(response, escape("<script>private-marker</script>"))
        self.assertNotContains(response, "<script>private-marker</script>")
        self.draft.refresh_from_db()
        self.assertFalse(self.draft.is_published)
        self.assertEqual(
            Client().get(reverse("article_page", args=[self.draft.pk])).status_code,
            404,
        )

    def test_owner_pages_are_not_cached(self):
        self.client.force_login(self.owner)
        for url in self.read_routes():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assert_private_cache_policy(response)

    def test_post_logout_clears_the_owner_session(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("writer_logout"))

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assert_login_redirect(
            self.client.get(reverse("writer_dashboard")), reverse("writer_dashboard")
        )

    def test_dashboard_search_and_status_filter_keep_global_counts(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("writer_dashboard"),
            {"q": "  private-marker  ", "status": "draft"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], "private-marker")
        self.assertEqual(response.context["status"], "draft")
        self.assertEqual(
            [article.pk for article in response.context["articles"]],
            [self.draft.pk],
        )
        self.assertEqual(
            response.context["counts"], {"total": 2, "published": 1, "drafts": 1}
        )

        response = self.client.get(
            reverse("writer_dashboard"), {"status": "published"}
        )
        self.assertEqual(
            [article.pk for article in response.context["articles"]],
            [self.published.pk],
        )
        self.assertEqual(
            self.client.get(
                reverse("writer_dashboard"), {"status": "archived"}
            ).status_code,
            400,
        )

    def test_owner_inventory_paginates_and_includes_drafts(self):
        self.client.force_login(self.owner)
        for number in range(9):
            post.objects.create(
                title=f"Published inventory article {number}",
                body="Inventory content.",
                is_published=True,
            )
        post.objects.all().update(created_at=self.draft.created_at)

        response = self.client.get(reverse("writer_dashboard"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page"].number, 2)
        self.assertFalse(response.context["page"].has_next())
        self.assertEqual(
            [article.pk for article in response.context["articles"]],
            [self.draft.pk],
        )
        self.assertEqual(
            response.context["counts"], {"total": 11, "published": 10, "drafts": 1}
        )

    def test_real_csrf_checks_reject_unsafe_posts_and_allow_a_tokenized_save(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        before = self.article_snapshot()
        for url, data in self.mutation_routes():
            with self.subTest(url=url):
                response = csrf_client.post(url, data)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(self.article_snapshot(), before)

        response = csrf_client.get(reverse("writer_new"))
        self.assertEqual(response.status_code, 200)
        csrf_cookie = csrf_client.cookies.get(settings.CSRF_COOKIE_NAME)
        self.assertIsNotNone(csrf_cookie)

        response = csrf_client.post(
            reverse("writer_new"),
            {
                "title": "CSRF protected draft",
                "body": "Saved with a real CSRF token.",
                "action": "save",
                "csrfmiddlewaretoken": csrf_cookie.value,
            },
        )

        article = post.objects.get(title="CSRF protected draft")
        self.assertFalse(article.is_published)
        self.assertRedirects(
            response,
            self.writer_url("writer_edit", article),
            fetch_redirect_response=False,
        )
