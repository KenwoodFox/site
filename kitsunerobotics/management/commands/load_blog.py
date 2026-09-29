import logging

from django.core.management.base import BaseCommand

from kitsunerobotics.blog_loader import pull_blog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Pull the blog repo and update posts from its contents"

    def handle(self, *args, **options):
        result = pull_blog()
        if result is None:
            logger.info("Blog repo is unchanged.")
            return
        slugs, removed = result
        logger.info("Loaded %s post(s), removed %s article(s).", len(slugs), removed)
