from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from .models import post

class PostListTests(TestCase):
    def test_search_returns_only_matching_published_posts(self):
        matching = post.objects.create(
            title="Python for DevOps",
            body="A published Python article.",
            is_published=True,
        )

        post.objects.create(
            title="Python draft",
            body="An unpublished Python article.",
            is_published=False,
        )

        post.objects.create(
            title="Linux networking",
            body="An unrelated published article.",
            is_published=True,
        )

        url = reverse("blog:post_list")
        response = self.client.get(url, {"q": "  pYtHoN  "})

        self.assertEqual(response.status_code, 200)

        results = response.json()["posts"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], matching.pk)

class PostDetailTests(TestCase):
    def test_draft_post_returns_404(self):
        draft = post.objects.create(
            title="Draft article",
            body="This article is not ready.",
            is_published=False,
        )

        url = reverse("blog:post_detail", args=[draft.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Post not found"})

    def test_published_post_returns_200(self):
        article = post.objects.create(
            title="Python and DevOps",
            body="My first published article.",
            is_published=True,
        )

        url = reverse("blog:post_detail", args=[article.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["post"]["id"], article.pk)
        self.assertEqual(data["post"]["title"], article.title)

class PostPaginationTests(TestCase):
    def test_second_page_contains_remaining_post(self):
        for number in range(6):
            post.objects.create(
                title=f"Article {number}",
                body="A published article.",
                is_published=True,
            )

        post.objects.create(
            title="Draft",
            body="A private article.",
            is_published=False,
        )

        url = reverse("blog:post_list")
        response = self.client.get(url, {"page": 2})

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["posts"]), 1)
        self.assertEqual(data["pagination"]["page"], 2)
        self.assertEqual(data["pagination"]["total"], 6)
        self.assertFalse(data["pagination"]["has_next"])

    def test_invalid_page_returns_400(self):
        url = reverse("blog:post_list")
        response = self.client.get(url, {"page": "abc"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid page"})     

class PostEdgeCaseTests(TestCase):
    def test_deleted_post_returns_404(self):
        article = post.objects.create(
            title="Deleted article",
            body="This article will be deleted.",
            is_published=True,
        )

        url = reverse("blog:post_detail", args=[article.pk])
        article.delete()

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Post not found"})

    def test_empty_list_returns_200(self):
        url = reverse("blog:post_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["posts"], [])
        self.assertEqual(data["pagination"]["total"], 0)  


class BlogPageTests(TestCase):
    def setUp(self):
        self.public = post.objects.create(
            title="Python & Linux notes",
            body="First line.\n<script>alert('example')</script>",
            is_published=True,
        )
        self.draft = post.objects.create(
            title="Python & Linux private draft",
            body="This article is not public.",
            is_published=False,
        )

    def test_home_shows_public_articles_and_hides_drafts(self):
        response = self.client.get(reverse("home"))

        self.assertTemplateUsed(response, "blog/home.html")
        self.assertContains(response, escape(self.public.title))
        self.assertNotContains(response, escape(self.draft.title))
        article_url = reverse("article_page", args=[self.public.pk])
        self.assertContains(response, f'href="{article_url}"')

    def test_search_pagination_link_preserves_query_and_opens_next_page(self):
        for number in range(5):
            post.objects.create(
                title=f"Python & Linux {number}",
                body="A matching published article.",
                is_published=True,
            )
        unrelated = post.objects.create(
            title="Networking basics",
            body="An unrelated published article.",
            is_published=True,
        )
        post.objects.filter(
            is_published=True, title__icontains="Python & Linux"
        ).update(created_at=self.public.created_at)

        query = "  pYtHoN & LiNuX  "
        response = self.client.get(reverse("home"), {"q": query})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], query.strip())
        self.assertEqual(response.context["page"].paginator.count, 6)
        self.assertEqual(len(response.context["articles"]), 5)
        self.assertNotContains(response, escape(self.draft.title))
        self.assertNotContains(response, unrelated.title)

        class NextLinkParser(HTMLParser):
            next_url = None

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == "a" and attributes.get("rel") == "next":
                    self.next_url = attributes.get("href")

        parser = NextLinkParser()
        parser.feed(response.content.decode())
        self.assertIsNotNone(parser.next_url)
        parameters = parse_qs(urlsplit(parser.next_url).query)
        self.assertEqual(parameters["q"], [query])
        self.assertEqual(parameters["page"], ["2"])

        response = self.client.get(urljoin(reverse("home"), parser.next_url))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page"].number, 2)
        self.assertEqual(response.context["page"].paginator.count, 6)
        self.assertEqual(
            [article.pk for article in response.context["articles"]],
            [self.public.pk],
        )

    def test_public_article_page_displays_escaped_body(self):
        response = self.client.get(
            reverse("article_page", args=[self.public.pk])
        )

        self.assertTemplateUsed(response, "blog/article_detail.html")
        self.assertContains(response, escape(self.public.title))
        self.assertContains(response, "First line.")
        self.assertContains(response, escape("<script>alert('example')</script>"))
        self.assertNotContains(response, "<script>alert('example')</script>")

    def test_draft_article_page_returns_404(self):
        response = self.client.get(
            reverse("article_page", args=[self.draft.pk])
        )

        self.assertEqual(response.status_code, 404)
