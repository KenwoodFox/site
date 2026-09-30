from django import template
from django.conf import settings

from kitsunerobotics.models import preview_for, tags_for

register = template.Library()


@register.filter
def post_tags(article):
    return tags_for(article)


@register.filter
def post_preview(article):
    return preview_for(article)


@register.filter
def absolute_url(path):
    if not path:
        return ""
    if path.startswith(("http://", "https://")):
        return path
    return settings.SITE_URL.rstrip("/") + "/" + path.lstrip("/")
