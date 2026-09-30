from django import template

from kitsunerobotics.models import tags_for

register = template.Library()


@register.filter
def post_tags(article):
    return tags_for(article)
