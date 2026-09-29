from django.test import TestCase
from django.urls import reverse

from apps.users.models import CustomUser
from kitsunerobotics.models import Comment, SiteSetting
from kitsunerobotics.views.blog import send_comment_webhook
from siteblog.models import Article


class CommentTests(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="Hello",
            slug="hello",
            article_body="A post",
            status="published",
        )
        self.verified = CustomUser.objects.create_user(
            "verified", "a@example.com", "pass", email_verified=True
        )
        self.unverified = CustomUser.objects.create_user(
            "plain", "b@example.com", "pass", email_verified=False
        )

    def test_verified_comment_is_visible(self):
        self.client.force_login(self.verified)
        self.client.post(reverse("post_comment", args=["hello"]), {"body": "Nice post"})
        response = self.client.get(self.article.get_absolute_url())
        self.assertContains(response, "Nice post")
        comment = Comment.objects.get()
        self.assertEqual(comment.author_name, "verified")
        self.assertTrue(comment.approved)

    def test_unverified_comment_waits_for_approval(self):
        self.client.force_login(self.unverified)
        self.client.post(reverse("post_comment", args=["hello"]), {"body": "Hidden note"})
        response = self.client.get(self.article.get_absolute_url())
        self.assertNotContains(response, "Hidden note")
        comment = Comment.objects.get()
        self.assertEqual(comment.author_name, "Unverified")
        self.assertFalse(comment.approved)

    def test_anonymous_comment_waits_for_approval(self):
        self.client.post(reverse("post_comment", args=["hello"]), {"body": "Anon note"})
        response = self.client.get(self.article.get_absolute_url())
        self.assertNotContains(response, "Anon note")
        comment = Comment.objects.get()
        self.assertEqual(comment.author_name, "Anonymous")
        self.assertIsNone(comment.user)
        self.assertFalse(comment.approved)

    def test_staff_can_preview_a_draft(self):
        Article.objects.create(
            title="Secret",
            slug="secret",
            article_body="Not yet",
            status="draft",
        )
        staff = CustomUser.objects.create_user(
            "staff", "s@example.com", "pass", is_staff=True
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("article_detail", args=["secret"]))
        self.assertContains(response, "Not yet")
        self.assertContains(response, "!!DRAFT!!")
        listing = self.client.get(reverse("blog_list"))
        self.assertContains(listing, "secret")

    def test_comment_on_a_draft_stays_on_the_post(self):
        Article.objects.create(
            title="Secret",
            slug="secret",
            article_body="Not yet",
            status="draft",
        )
        staff = CustomUser.objects.create_user(
            "editor", "e@example.com", "pass", is_staff=True, email_verified=True
        )
        self.client.force_login(staff)
        response = self.client.post(reverse("post_comment", args=["secret"]), {"body": "Hi"})
        self.assertRedirects(
            response,
            reverse("article_detail", args=["secret"]) + "#comments",
            fetch_redirect_response=False,
        )

    def test_feed_lists_published_posts(self):
        Article.objects.create(
            title="Secret",
            slug="secret",
            article_body="Hidden",
            status="draft",
        )
        response = self.client.get(reverse("blog_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/rss+xml", response["Content-Type"])
        self.assertContains(response, "Hello")
        self.assertNotContains(response, "Secret")

    def test_public_cannot_see_a_draft(self):
        Article.objects.create(
            title="Secret",
            slug="secret",
            article_body="Not yet",
            status="draft",
        )
        response = self.client.get(reverse("article_detail", args=["secret"]))
        self.assertEqual(response.status_code, 404)
        listing = self.client.get(reverse("blog_list"))
        self.assertNotContains(listing, "Secret")

    def test_missing_webhook_setting_is_created_as_none(self):
        comment = Comment.objects.create(
            article=self.article,
            author_name="Anonymous",
            body="Hi",
            approved=False,
        )
        send_comment_webhook(comment)
        setting = SiteSetting.objects.get(key="blogpost_webhook")
        self.assertEqual(setting.value, "None")
