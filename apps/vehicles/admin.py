from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "brand", "model", "year", "client", "engine_type", "expiry_date", "is_active", "created_at"]
    list_filter = ["engine_type", "is_active", "created_at"]
    search_fields = ["plate_number", "brand", "model", "vin", "client__full_name"]
    readonly_fields = ["created_at", "updated_at", "deleted_at", "created_by"]
    ordering = ["-created_at"]
    raw_id_fields = ["client"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
