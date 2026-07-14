from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["client", "amount", "payment_date", "payment_method", "status", "vehicle", "created_at"]
    list_filter = ["status", "payment_method", "payment_date"]
    search_fields = ["client__full_name", "client__phone", "vehicle__plate_number"]
    readonly_fields = ["created_at", "updated_at", "deleted_at", "created_by"]
    ordering = ["-payment_date"]
    raw_id_fields = ["client", "vehicle", "inspection"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
