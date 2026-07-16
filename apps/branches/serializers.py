from rest_framework import serializers

from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    employees_count = serializers.SerializerMethodField()
    clients_count = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            "id", "name", "address",
            "is_active", "employees_count", "clients_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_employees_count(self, obj) -> int:
        return getattr(obj, "_employees_count", obj.employees_count)

    def get_clients_count(self, obj) -> int:
        return getattr(obj, "_clients_count", obj.clients_count)


class BranchMinimalSerializer(serializers.ModelSerializer):
    """Boshqa serializerlarda nested ishlatish uchun."""

    class Meta:
        model = Branch
        fields = ["id", "name", "code"]
