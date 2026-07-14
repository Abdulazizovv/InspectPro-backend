from rest_framework import serializers


class OverviewSerializer(serializers.Serializer):
    total_clients = serializers.IntegerField()
    total_vehicles = serializers.IntegerField()
    today_inspections = serializers.IntegerField()
    upcoming_expirations = serializers.IntegerField()
    expires_15_days = serializers.IntegerField()
    expired_vehicles = serializers.IntegerField()
    monthly_revenue = serializers.CharField()
    total_employees = serializers.IntegerField()
    new_vehicles_this_month = serializers.IntegerField()
    inspections_change = serializers.IntegerField()
    revenue_change = serializers.CharField()


class MonthlyInspectionSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    count = serializers.IntegerField()


class MonthlyRevenueSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    amount = serializers.FloatField()


class ExpiringSoonVehicleSerializer(serializers.Serializer):
    vehicle_id = serializers.CharField()
    plate_number = serializers.CharField()
    client_name = serializers.CharField()
    client_phone = serializers.CharField()
    expiry_date = serializers.CharField(allow_null=True)
    gas_cylinder_expiry_date = serializers.CharField(allow_null=True, required=False)
    days_left = serializers.IntegerField()
    inspection_type = serializers.CharField()
    sms_status = serializers.CharField(allow_null=True)


class DashboardStatsSerializer(serializers.Serializer):
    overview = OverviewSerializer()
    monthly_inspections = MonthlyInspectionSerializer(many=True)
    monthly_revenue = MonthlyRevenueSerializer(many=True)
    expiring_soon = ExpiringSoonVehicleSerializer(many=True)
    recent_activities = serializers.ListField(child=serializers.DictField())
