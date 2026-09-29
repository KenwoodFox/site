import re

import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

IMAGE = re.compile(r"<img\b[^>]*\bsrc=\"([^\"]+)\"[^>]*>")
MEDIA_LINK = re.compile(r"<a href=\"(/media/[^\"]+)\">([^<]*)</a>")


def _images(html):
    def replace(match):
        src = match.group(1)
        return f'<a class="post-image" href="{src}">{match.group(0)}</a>'

    return IMAGE.sub(replace, html)


def _downloads(html):
    def replace(match):
        href, text = match.group(1), match.group(2).strip()
        name = text or href.rsplit("/", 1)[-1]
        return (
            f'<a class="download-box" href="{href}" download>'
            f"Download <span>{name}</span></a>"
        )

    return MEDIA_LINK.sub(replace, html)


@register.filter
def render_markdown(value):
    text = getattr(value, "content", None)
    if text is None:
        text = "" if value is None else str(value)
    html = markdown.markdown(text, extensions=["extra", "fenced_code"])
    return mark_safe(_downloads(_images(html)))
