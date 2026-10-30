from django.test import TestCase
from django.urls import reverse

from .models import post


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
# Create your tests here.
