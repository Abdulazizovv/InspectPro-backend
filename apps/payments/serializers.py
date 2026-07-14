from rest_framework import serializers

from .models import Payment


class PaymentListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    client_phone = serializers.CharField(source="client.phone", read_only=True)
    vehicle_plate = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "client", "client_name", "client_phone",
            "vehicle", "vehicle_plate",
            "amount", "payment_date",
            "payment_method", "payment_method_display",
            "status", "status_display",
            "created_at",
        ]

    def get_vehicle_plate(self, obj) -> str:
        return obj.vehicle.plate_number if obj.vehicle else ""


class PaymentDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    client_phone = serializers.CharField(source="client.phone", read_only=True)
    vehicle_plate = serializers.SerializerMethodField()
    vehicle_brand = serializers.SerializerMethodField()
    inspection_date = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id", "client", "client_name", "client_phone",
            "vehicle", "vehicle_plate", "vehicle_brand",
            "inspection", "inspection_date",
            "amount", "payment_date",
            "payment_method", "payment_method_display",
            "status", "status_display",
            "notes", "created_by_name", "created_at", "updated_at",
        ]

    def get_vehicle_plate(self, obj) -> str:
        return obj.vehicle.plate_number if obj.vehicle else ""

    def get_vehicle_brand(self, obj) -> str:
        if obj.vehicle:
            return f"{obj.vehicle.brand} {obj.vehicle.model}"
        return ""

    def get_inspection_date(self, obj) -> str:
        return str(obj.inspection.inspection_date) if obj.inspection else ""

    def get_created_by_name(self, obj) -> str:
        return obj.created_by.full_name if obj.created_by else ""


class PaymentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "client", "vehicle", "inspection",
            "amount", "payment_date",
            "payment_method", "status", "notes",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Summa 0 dan katta bo'lishi kerak.")
        return value
