from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "passport", "is_active", "created_by", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["full_name", "phone", "passport"]
    readonly_fields = ["created_at", "updated_at", "deleted_at", "created_by"]
    ordering = ["-created_at"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
