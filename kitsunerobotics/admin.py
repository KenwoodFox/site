from django.contrib import admin
from .models import Comment, SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """So you can edit site settings in the admin page."""

    list_display = ("key", "value")
    search_fields = ("key", "value")


@admin.action(description="Approve selected comments")
def approve_comments(modeladmin, request, queryset):
    queryset.update(approved=True)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author_name", "article", "approved", "created_at", "user")
    list_editable = ("approved",)
    list_filter = ("approved",)
    search_fields = ("body", "author_name")
    actions = (approve_comments,)
