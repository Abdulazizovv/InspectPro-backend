from django.contrib import admin

from .models import SmsReminder, SmsTemplate


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "days_before", "is_active", "created_at"]
    list_filter = ["is_active", "days_before"]
    search_fields = ["name", "body"]
    readonly_fields = ["created_at", "updated_at", "deleted_at"]


@admin.register(SmsReminder)
class SmsReminderAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "phone", "scheduled_date", "status", "trigger_type", "sent_at", "created_at"]
    list_filter = ["status", "trigger_type", "scheduled_date"]
    search_fields = ["vehicle__plate_number", "vehicle__client__full_name", "phone"]
    readonly_fields = ["sent_at", "error_message", "created_at", "updated_at", "deleted_at"]
    ordering = ["-scheduled_date"]
