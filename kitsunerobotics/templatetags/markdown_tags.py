import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def render_markdown(value):
    text = getattr(value, "content", None)
    if text is None:
        text = "" if value is None else str(value)
    html = markdown.markdown(text, extensions=["extra", "fenced_code"])
    return mark_safe(html)
