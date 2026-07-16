from django.contrib import admin

from .models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "phone", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "code", "address", "phone"]
    readonly_fields = ["id", "created_at", "updated_at", "created_by"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
