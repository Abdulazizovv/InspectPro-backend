from rest_framework import serializers

from apps.common.validators import validate_same_branch
from .models import Vehicle


class VehicleListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    client_phone = serializers.CharField(source="client.phone", read_only=True)
    engine_type_display = serializers.CharField(source="get_engine_type_display", read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    is_gas_vehicle = serializers.SerializerMethodField()
    days_until_gas_cylinder_expiry = serializers.SerializerMethodField()
    is_gas_cylinder_expired = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id", "client", "client_name", "client_phone",
            "brand", "model", "year", "plate_number",
            "engine_type", "engine_type_display",
            "expiry_date", "is_expired", "days_until_expiry",
            "gas_cylinder_expiry_date", "days_until_gas_cylinder_expiry", "is_gas_cylinder_expired",
            "is_gas_vehicle",
            "is_active", "created_at",
        ]

    def get_is_expired(self, obj) -> bool:
        from django.utils import timezone
        if not obj.expiry_date:
            return False
        return obj.expiry_date < timezone.localdate()

    def get_days_until_expiry(self, obj) -> int | None:
        from django.utils import timezone
        if not obj.expiry_date:
            return None
        delta = obj.expiry_date - timezone.localdate()
        return delta.days

    def get_is_gas_vehicle(self, obj) -> bool:
        return obj.engine_type in ("metan", "propan")

    def get_days_until_gas_cylinder_expiry(self, obj) -> int | None:
        from django.utils import timezone
        if not obj.gas_cylinder_expiry_date:
            return None
        return (obj.gas_cylinder_expiry_date - timezone.localdate()).days

    def get_is_gas_cylinder_expired(self, obj) -> bool:
        from django.utils import timezone
        if not obj.gas_cylinder_expiry_date:
            return False
        return obj.gas_cylinder_expiry_date < timezone.localdate()


class VehicleDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    client_phone = serializers.CharField(source="client.phone", read_only=True)
    engine_type_display = serializers.CharField(source="get_engine_type_display", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    is_gas_vehicle = serializers.SerializerMethodField()
    days_until_gas_cylinder_expiry = serializers.SerializerMethodField()
    is_gas_cylinder_expired = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id", "client", "client_name", "client_phone",
            "brand", "model", "year", "plate_number", "vin", "color",
            "engine_type", "engine_type_display",
            "last_inspection_date", "expiry_date",
            "is_expired", "days_until_expiry",
            "gas_cylinder_expiry_date", "days_until_gas_cylinder_expiry", "is_gas_cylinder_expired",
            "is_gas_vehicle",
            "is_active", "notes",
            "created_by_name", "created_at", "updated_at",
        ]

    def get_created_by_name(self, obj) -> str:
        return obj.created_by.full_name if obj.created_by else ""

    def get_is_expired(self, obj) -> bool:
        from django.utils import timezone
        if not obj.expiry_date:
            return False
        return obj.expiry_date < timezone.localdate()

    def get_days_until_expiry(self, obj) -> int | None:
        from django.utils import timezone
        if not obj.expiry_date:
            return None
        return (obj.expiry_date - timezone.localdate()).days

    def get_is_gas_vehicle(self, obj) -> bool:
        return obj.engine_type in ("metan", "propan")

    def get_days_until_gas_cylinder_expiry(self, obj) -> int | None:
        from django.utils import timezone
        if not obj.gas_cylinder_expiry_date:
            return None
        return (obj.gas_cylinder_expiry_date - timezone.localdate()).days

    def get_is_gas_cylinder_expired(self, obj) -> bool:
        from django.utils import timezone
        if not obj.gas_cylinder_expiry_date:
            return False
        return obj.gas_cylinder_expiry_date < timezone.localdate()


class VehicleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "client", "brand", "model", "year", "plate_number", "vin",
            "color", "engine_type", "last_inspection_date", "expiry_date",
            "gas_cylinder_expiry_date",
            "is_active", "notes",
        ]

    def validate_client(self, value):
        validate_same_branch(self.context.get("request"), value, "mijoz")
        return value

    def validate_plate_number(self, value: str) -> str:
        return value.upper().strip()

    def validate_year(self, value: int) -> int:
        from django.utils import timezone
        current_year = timezone.now().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(f"Yil 1900 va {current_year + 1} oralig'ida bo'lishi kerak.")
        return value
