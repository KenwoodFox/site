from django.test import TestCase
from django.urls import reverse


class MainPageTests(TestCase):
    def test_home_page_loads(self):
        """Test that the home page loads successfully."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_tools_page_loads(self):
        """Test that the tools/apps page loads successfully."""
        response = self.client.get(reverse("tools"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My tools")
        self.assertContains(response, "https://nextcloud.kitsunehosting.net/")
        self.assertContains(response, "https://bitwarden.kitsunehosting.net/")
        self.assertContains(response, "https://git.kitsunehosting.net/")
        self.assertContains(response, "Zinc")
        self.assertContains(response, "Vaultwarden")
        self.assertContains(response, "Gitea")
        self.assertContains(response, "cutopt")

    def test_blog_page_loads(self):
        """Test that the blog page loads successfully."""
        response = self.client.get(reverse("blog_list"))
        self.assertEqual(response.status_code, 200)

    def test_store_page_loads(self):
        """Test that the store page loads successfully."""
        response = self.client.get(reverse("store:store_list"))
        self.assertEqual(response.status_code, 200)

    def test_user_gallery_page_loads(self):
        """Test that the user gallery page loads successfully."""
        response = self.client.get(reverse("user-gallery"))
        self.assertEqual(response.status_code, 200)
