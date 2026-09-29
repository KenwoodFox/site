from django.conf import settings
from django.db import models


class SiteSetting(models.Model):
    """
    Site setting can store dedicated simple things. Easier than editing
    a bunch of ENV variables on the host side!
    """

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"{self.key}: {self.value}"


class Comment(models.Model):
    article = models.ForeignKey(
        "siteblog.Article", on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="article_comments",
    )
    author_name = models.CharField(max_length=150)
    body = models.TextField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author_name} on {self.article}"
