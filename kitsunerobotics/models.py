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


class ArticleTags(models.Model):
    article = models.OneToOneField(
        "siteblog.Article",
        on_delete=models.CASCADE,
        related_name="article_tags",
    )
    names = models.JSONField(default=list, blank=True)
    preview = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        verbose_name = "Article tags"
        verbose_name_plural = "Article tags"

    def __str__(self):
        return ", ".join(self.names)


def tags_for(article):
    try:
        names = article.article_tags.names
    except ArticleTags.DoesNotExist:
        return []
    return list(names or [])


def preview_for(article):
    try:
        return article.article_tags.preview or ""
    except ArticleTags.DoesNotExist:
        return ""


def filter_by_tag(articles, tag):
    """Keep articles whose stored tag list includes tag.

    Tags live in a JSON list. SQLite cannot run a JSON contains lookup, so
    match in Python and then restrict the queryset.
    """
    if not tag:
        return articles
    matching = [
        row.article_id
        for row in ArticleTags.objects.filter(article_id__in=articles.values("pk"))
        if tag in (row.names or [])
    ]
    return articles.filter(pk__in=matching)


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
