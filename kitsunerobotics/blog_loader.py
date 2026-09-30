import re
import subprocess
from datetime import datetime, time
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from kitsunerobotics.models import ArticleTags, tags_for
from kitsunerobotics.webhooks import notify_post_removed, notify_post_update
from siteblog.models import Article

LINK = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")


def parse_post(text):
    """Split a markdown file into frontmatter fields and the body."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip()
    return meta, parts[2].lstrip("\n")


def parse_tags(value):
    if not value:
        return []
    return [part for part in re.split(r"[\s,]+", value) if part]


def published_on(value):
    if not value:
        return timezone.now()
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return timezone.now()
    return timezone.make_aware(datetime.combine(day, time(12, 0)))


def rewrite_links(body, markdown_path, repo_root):
    """Point a repo-relative link at the same path under /media/."""
    repo_root = repo_root.resolve()

    def replace(match):
        label, target = match.group(1), match.group(2).strip()
        if target.startswith(("http://", "https://", "/", "#", "mailto:")):
            return match.group(0)
        source = (markdown_path.parent / target).resolve()
        if not source.is_file() or not source.is_relative_to(repo_root):
            return match.group(0)
        relative = source.relative_to(repo_root)
        url = f"{settings.MEDIA_URL.rstrip('/')}/blog/{relative.as_posix()}"
        return f"{label}({url})"

    return LINK.sub(replace, body)


def article_body(article):
    body = article.article_body
    content = getattr(body, "content", None)
    if content is None:
        return "" if body is None else str(body)
    return content


def load_posts(repo_root):
    """Create or update articles from markdown files. Remove articles the repo dropped."""
    repo_root = Path(repo_root)
    slugs = []
    for markdown_path in sorted(repo_root.rglob("*.md")):
        if ".git" in markdown_path.parts or markdown_path.name.lower() == "readme.md":
            continue
        text = markdown_path.read_text(encoding="utf-8")
        meta, body = parse_post(text)
        slug = slugify(meta.get("slug") or markdown_path.stem)[:50]
        if not slug:
            continue
        title = meta.get("title") or markdown_path.stem
        status = meta.get("status", "draft").lower()
        if status not in ("draft", "published"):
            status = "draft"
        body = rewrite_links(body, markdown_path, repo_root)
        tags = parse_tags(meta.get("tags"))
        raw_published = meta.get("published")
        when = published_on(raw_published) if raw_published else None
        article = Article.objects.filter(slug=slug).first()
        created = article is None
        if when is None:
            when = timezone.now() if created else article.published_on
        if created:
            article = Article.objects.create(
                slug=slug,
                title=title,
                article_body=body,
                status=status,
                published_on=when,
            )
        previous_tags = [] if created else tags_for(article)
        changed = created or (
            article.title != title
            or article_body(article) != body
            or article.status != status
            or article.published_on != when
            or previous_tags != tags
        )
        if changed:
            article.title = title
            article.article_body = body
            article.status = status
            article.published_on = when
            article.save()
            ArticleTags.objects.update_or_create(
                article=article, defaults={"names": tags}
            )
            notify_post_update(article, created, tags)
        slugs.append(slug)

    removed_articles = list(Article.objects.exclude(slug__in=slugs))
    for article in removed_articles:
        notify_post_removed(article)
    removed, _details = Article.objects.filter(
        pk__in=[article.pk for article in removed_articles]
    ).delete()
    return slugs, removed


def git(*args):
    subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def remote_head(url):
    result = subprocess.run(
        ["git", "ls-remote", url, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    line = result.stdout.strip().split()
    if not line:
        raise RuntimeError(f"No HEAD on {url}")
    return line[0]


def local_head(checkout):
    result = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def pull_blog(url=None, checkout=None):
    """Download the repo only when its latest commit changed.

    Returns None when the checkout is already current, otherwise the
    (slugs, removed) result from load_posts.
    """
    url = url or settings.BLOG_REPO_URL
    checkout = Path(checkout or Path(settings.MEDIA_ROOT) / "blog")
    remote = remote_head(url)
    if (checkout / ".git").is_dir() and local_head(checkout) == remote:
        return None

    checkout.mkdir(parents=True, exist_ok=True)
    if not (checkout / ".git").is_dir():
        git("-C", str(checkout), "init")
        git("-C", str(checkout), "remote", "add", "origin", url)
    git("-C", str(checkout), "fetch", "--depth", "1", "origin")
    git("-C", str(checkout), "reset", "--hard", "FETCH_HEAD")
    git("-C", str(checkout), "clean", "-fd")
    return load_posts(checkout)
