from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import ListView

from siteblog.models import Article


class ArticleListView(ListView):
    template_name = "siteblog/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        site = get_current_site(self.request)
        return Article.objects.published().visible_on_site(site)
