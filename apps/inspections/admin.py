from django.contrib import admin
from .models import Inspection


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "inspection_date", "expiry_date", "status", "inspector", "created_at"]
    list_filter = ["status", "inspection_date"]
    search_fields = ["vehicle__plate_number", "vehicle__brand", "vehicle__client__full_name"]
    readonly_fields = ["created_at", "updated_at", "deleted_at", "created_by"]
    ordering = ["-inspection_date"]
    raw_id_fields = ["vehicle", "inspector"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
