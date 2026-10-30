from django.test import TestCase
from django.urls import reverse

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
# Create your tests here.
