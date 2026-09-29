import logging

import markdown
import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from kitsunerobotics.models import Comment, SiteSetting
from siteblog.models import Article

logger = logging.getLogger(__name__)


class CommentForm(forms.Form):
    body = forms.CharField(
        label="Comment",
        widget=forms.Textarea(attrs={"rows": 4}),
        max_length=4000,
    )


def comment_identity(user):
    if user.is_authenticated and getattr(user, "email_verified", False):
        return user.username, True
    if user.is_authenticated:
        return "Unverified", False
    return "Anonymous", False


def send_comment_webhook(comment):
    setting, _created = SiteSetting.objects.get_or_create(
        key="blogpost_webhook",
        defaults={"value": "None"},
    )
    url = setting.value.strip()
    if not url or url == "None":
        return
    needs_approval = "" if comment.approved else " (needs approval)"
    message = (
        f"New comment{needs_approval} on {comment.article.title}\n"
        f"{comment.author_name}: {comment.body[:500]}\n"
        f"{settings.SITE_URL}{reverse('article_detail', args=[comment.article.slug])}"
    )
    try:
        response = requests.post(url, json={"content": message}, timeout=5)
        response.raise_for_status()
    except Exception:
        logger.exception("Discord webhook failed for comment %s", comment.pk)


def articles_for_request(request):
    site = get_current_site(request)
    articles = Article.objects.visible_on_site(site)
    if request.user.is_staff:
        return articles
    return articles.published()


class ArticleListView(ListView):
    template_name = "siteblog/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        return articles_for_request(self.request)


class ArticleDetailView(DetailView):
    model = Article
    template_name = "siteblog/article_detail.html"
    context_object_name = "article"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return articles_for_request(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.filter(approved=True)
        context["comment_form"] = CommentForm()
        return context


@require_POST
def post_comment(request, slug):
    article = get_object_or_404(articles_for_request(request), slug=slug)
    form = CommentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Say something first.")
        return redirect(reverse("article_detail", args=[article.slug]) + "#comments")

    author_name, approved = comment_identity(request.user)
    comment = Comment.objects.create(
        article=article,
        user=request.user if request.user.is_authenticated else None,
        author_name=author_name,
        body=form.cleaned_data["body"].strip(),
        approved=approved,
    )
    send_comment_webhook(comment)
    if approved:
        messages.success(request, "Posted.")
    else:
        messages.success(request, "Got it. I'll look this over before it shows.")
    return redirect(reverse("article_detail", args=[article.slug]) + "#comments")


class ArticleFeed(Feed):
    title = "KitsuneHosting"
    link = "/blog/"
    description = "Posts from KitsuneHosting"

    def get_object(self, request, *args, **kwargs):
        self.site = get_current_site(request)
        return None

    def items(self):
        return (
            Article.objects.published()
            .visible_on_site(self.site)
            .order_by("-published_on", "title")[:20]
        )

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return reverse("article_detail", args=[item.slug])

    def item_pubdate(self, item):
        return item.published_on

    def item_description(self, item):
        body = item.article_body
        text = body.excerpt or getattr(body, "content", "")
        return markdown.markdown(text or "", extensions=["extra", "fenced_code"])
