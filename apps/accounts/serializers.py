from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


# ──────────────────────────────── Employee (User CRUD) ────────────────────────

class EmployeeListSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    inspection_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "phone",
            "role", "role_display", "is_active",
            "inspection_count", "created_at",
        ]

    def get_inspection_count(self, obj) -> int:
        return getattr(obj, "inspection_count", 0)


class EmployeeDetailSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "phone",
            "role", "role_display", "avatar", "is_active",
            "created_at", "updated_at",
        ]


class EmployeeWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "role", "is_active", "password"]

    def validate_password(self, value: str) -> str:
        if value:
            validate_password(value)
        return value

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "Yangi xodim uchun parol kiritilishi shart."})
        if not validated_data.get("email"):
            phone = validated_data.get("phone", "unknown")
            validated_data["email"] = f"user_{phone}@inspectpro.local"
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance: User, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone",
            "role", "role_display", "avatar",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "email", "role", "role_display", "created_at", "updated_at"]


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone", "avatar"]

    def validate_full_name(self, value: str) -> str:
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Ism kamida 2 ta belgidan iborat bo'lishi kerak.")
        return value.strip()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Parollar mos kelmadi."})
        return attrs
