from rest_framework import serializers

from apps.vehicles.models import Vehicle
from .models import SmsReminder, SmsTemplate


class SmsTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsTemplate
        fields = ["id", "name", "body", "days_before", "inspection_type", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SmsReminderListSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True, default=None)
    vehicle_brand = serializers.CharField(source="vehicle.brand", read_only=True, default=None)
    vehicle_model = serializers.CharField(source="vehicle.model", read_only=True, default=None)
    client_name = serializers.CharField(source="vehicle.client.full_name", read_only=True, default=None)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True, default=None)

    class Meta:
        model = SmsReminder
        fields = [
            "id",
            "vehicle_plate",
            "vehicle_brand",
            "vehicle_model",
            "client_name",
            "phone",
            "message",
            "scheduled_date",
            "sent_at",
            "status",
            "trigger_type",
            "inspection_type",
            "error_message",
            "created_by_name",
            "created_at",
        ]


class SmsReminderDetailSerializer(SmsReminderListSerializer):
    vehicle_id = serializers.UUIDField(source="vehicle.id", read_only=True)

    class Meta(SmsReminderListSerializer.Meta):
        fields = SmsReminderListSerializer.Meta.fields + ["vehicle_id", "updated_at"]


class SmsReminderWriteSerializer(serializers.ModelSerializer):
    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.filter(deleted_at__isnull=True),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = SmsReminder
        fields = ["id", "vehicle", "phone", "message", "scheduled_date", "trigger_type", "inspection_type"]
        read_only_fields = ["id"]

    def validate_phone(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Telefon raqami kiritilishi shart.")
        return cleaned
