from django.contrib.sites.shortcuts import get_current_site
from django.views import View
from django.shortcuts import render
from siteblog.models import Article


class HomeView(View):
    def get(self, request, *args, **kwargs):
        site = get_current_site(request)
        latest_posts = Article.objects.published().visible_on_site(site)[:6]

        context = {"latest_posts": latest_posts}

        return render(request, "home.html", context)
