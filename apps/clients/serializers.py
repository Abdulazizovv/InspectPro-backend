from rest_framework import serializers
from .models import Client


class ClientListSerializer(serializers.ModelSerializer):
    vehicle_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id", "full_name", "phone", "passport",
            "is_active", "vehicle_count", "created_at",
        ]

    def get_vehicle_count(self, obj) -> int:
        return obj.vehicle_count


class ClientDetailSerializer(serializers.ModelSerializer):
    vehicle_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id", "full_name", "phone", "passport", "address", "notes",
            "is_active", "vehicle_count", "created_by_name",
            "created_at", "updated_at",
        ]

    def get_vehicle_count(self, obj) -> int:
        return obj.vehicle_count

    def get_created_by_name(self, obj) -> str:
        return obj.created_by.full_name if obj.created_by else ""


class ClientWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["full_name", "phone", "passport", "address", "notes", "is_active"]

    def validate_phone(self, value: str) -> str:
        qs = Client.objects.filter(deleted_at__isnull=True, phone=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        return value
