from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import StoreItem


class StoreListView(ListView):
    model = StoreItem
    template_name = "store/store_list.html"
    context_object_name = "items"
    paginate_by = 12

    def get_queryset(self):
        queryset = StoreItem.objects.filter(status="published")

        # Search functionality
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        # Filter by availability
        in_stock_only = self.request.GET.get("in_stock", "")
        if in_stock_only == "true":
            queryset = queryset.filter(in_stock=True)

        return queryset.order_by("-published_at", "-created_at")


class StoreItemDetailView(DetailView):
    model = StoreItem
    template_name = "store/item_detail.html"
    context_object_name = "item"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return StoreItem.objects.filter(status="published")
