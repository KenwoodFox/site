from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("", views.StoreListView.as_view(), name="store_list"),
    path("item/<slug:slug>/", views.StoreItemDetailView.as_view(), name="item_detail"),
]
