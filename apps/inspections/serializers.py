from rest_framework import serializers

from .models import Inspection


class InspectionListSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)
    vehicle_brand = serializers.CharField(source="vehicle.brand", read_only=True)
    vehicle_model = serializers.CharField(source="vehicle.model", read_only=True)
    client_name = serializers.CharField(source="vehicle.client.full_name", read_only=True)
    client_id = serializers.CharField(source="vehicle.client_id", read_only=True)
    client_phone = serializers.CharField(source="vehicle.client.phone", read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    inspector_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    inspection_type_display = serializers.CharField(source="get_inspection_type_display", read_only=True)

    class Meta:
        model = Inspection
        fields = [
            "id", "vehicle", "vehicle_plate", "vehicle_brand", "vehicle_model",
            "client_name", "client_id", "client_phone",
            "inspection_date", "expiry_date",
            "inspection_type", "inspection_type_display",
            "status", "status_display", "inspector_name", "amount", "created_at",
        ]

    def get_inspector_name(self, obj) -> str:
        return obj.inspector.full_name if obj.inspector else ""


class InspectionDetailSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)
    vehicle_brand = serializers.CharField(source="vehicle.brand", read_only=True)
    vehicle_model = serializers.CharField(source="vehicle.model", read_only=True)
    vehicle_year = serializers.IntegerField(source="vehicle.year", read_only=True)
    client_name = serializers.CharField(source="vehicle.client.full_name", read_only=True)
    client_phone = serializers.CharField(source="vehicle.client.phone", read_only=True)
    client_id = serializers.CharField(source="vehicle.client_id", read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    inspector_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    inspection_type_display = serializers.CharField(source="get_inspection_type_display", read_only=True)

    class Meta:
        model = Inspection
        fields = [
            "id", "vehicle", "vehicle_plate", "vehicle_brand", "vehicle_model", "vehicle_year",
            "client_name", "client_phone", "client_id",
            "inspection_date", "expiry_date",
            "inspection_type", "inspection_type_display",
            "status", "status_display",
            "inspector", "inspector_name",
            "amount", "notes", "created_by_name", "created_at", "updated_at",
        ]

    def get_inspector_name(self, obj) -> str:
        return obj.inspector.full_name if obj.inspector else ""

    def get_created_by_name(self, obj) -> str:
        return obj.created_by.full_name if obj.created_by else ""


class InspectionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = [
            "vehicle", "inspection_date", "expiry_date",
            "inspection_type", "status", "inspector", "notes", "amount",
        ]

    def validate(self, attrs):
        status = attrs.get("status", self.instance.status if self.instance else Inspection.Status.SCHEDULED)
        expiry_date = attrs.get("expiry_date", self.instance.expiry_date if self.instance else None)

        if status == Inspection.Status.PASSED and not expiry_date:
            raise serializers.ValidationError(
                {"expiry_date": "Ko'rik 'o'tdi' bo'lganda yangi muddat kiritilishi shart."}
            )
        return attrs
