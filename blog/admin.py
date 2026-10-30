
from django.contrib import admin

from .models import post


@admin.register(post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_published", "created_at")
    list_display_links = ("id", "title")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "body")
    list_editable = ("is_published",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at", "-pk")
    list_per_page = 20
# Register your models here.
