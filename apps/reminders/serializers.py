from string import Formatter

from rest_framework import serializers

from apps.common.validators import validate_same_branch
from apps.vehicles.models import Vehicle
from .models import SMS_TEMPLATE_VARIABLES, SmsReminder, SmsTemplate


class SmsTemplateSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)

    class Meta:
        model = SmsTemplate
        fields = [
            "id", "name", "body", "days_before", "inspection_type",
            "branch", "branch_name", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "branch", "branch_name", "created_at", "updated_at"]

    def validate_body(self, value: str) -> str:
        """Reject typos before a template can be saved and used for an SMS."""
        try:
            fields = [field for _, field, _, _ in Formatter().parse(value) if field]
        except ValueError as exc:
            raise serializers.ValidationError("Shablondagi qavslar noto'g'ri yozilgan.") from exc

        invalid_fields = [field for field in fields if field not in SMS_TEMPLATE_VARIABLES]
        if invalid_fields:
            allowed = ", ".join(f"{{{name}}}" for name in sorted(SMS_TEMPLATE_VARIABLES))
            raise serializers.ValidationError(
                f"Noma'lum o'zgaruvchi: {', '.join(invalid_fields)}. Ruxsat etilganlari: {allowed}"
            )
        return value


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

    def validate_vehicle(self, value):
        validate_same_branch(self.context.get("request"), value, "avtomobil")
        return value
