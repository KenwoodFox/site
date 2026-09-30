import logging

import requests
from django.conf import settings
from django.urls import reverse

from kitsunerobotics.models import SiteSetting, tags_for

logger = logging.getLogger(__name__)

# I like webhooks!

def blog_webhook_url():
    setting, _created = SiteSetting.objects.get_or_create(
        key="blogpost_webhook",
        defaults={"value": "None"},
    )
    url = setting.value.strip()
    if not url or url == "None":
        return None
    return url


def send_blog_webhook(message):
    url = blog_webhook_url()
    if not url:
        return
    try:
        response = requests.post(url, json={"content": message}, timeout=5)
        response.raise_for_status()
    except Exception:
        logger.exception("Discord webhook failed")
        return
    logger.info("Sent Discord webhook: %s", message.split("\n", 1)[0])


def post_url(article):
    return f"{settings.SITE_URL}{reverse('article_detail', args=[article.slug])}"


def _with_tags(lines, tags):
    if tags:
        lines.append("tags: " + ", ".join(tags))
    return lines


def notify_post_update(article, created, tags):
    verb = "New blog post" if created else "Updated blog post"
    lines = _with_tags(
        [f"{verb}: {article.title}", f"status: {article.status}"],
        tags,
    )
    lines.append(post_url(article))
    send_blog_webhook("\n".join(lines))


def notify_post_removed(article):
    send_blog_webhook(f"Removed blog post: {article.title}\n{post_url(article)}")


def notify_comment(comment):
    needs_approval = "" if comment.approved else " (needs approval)"
    lines = _with_tags(
        [f"New comment{needs_approval} on {comment.article.title}"],
        tags_for(comment.article),
    )
    lines.append(f"{comment.author_name}: {comment.body[:500]}")
    lines.append(post_url(comment.article))
    send_blog_webhook("\n".join(lines))
