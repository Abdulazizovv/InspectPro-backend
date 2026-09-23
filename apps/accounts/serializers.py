from rest_framework import serializers

from .models import User, ActivityLog
from apps.branches.serializers import BranchMinimalSerializer


# ──────────────────────────────── Employee (User CRUD) ────────────────────────

class EmployeeListSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    inspection_count = serializers.SerializerMethodField()
    branch = BranchMinimalSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "full_name", "phone",
            "role", "role_display", "is_active",
            "branch", "inspection_count", "created_at",
        ]

    def get_inspection_count(self, obj) -> int:
        return getattr(obj, "inspection_count", 0)


class ActivityLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id", "action", "action_display", "target_type", "target_repr",
            "metadata", "ip_address", "created_at",
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    branch = BranchMinimalSerializer(read_only=True)
    activity_count = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    clients_count = serializers.SerializerMethodField()
    vehicles_count = serializers.SerializerMethodField()
    inspections_count = serializers.SerializerMethodField()
    sms_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "full_name", "phone",
            "role", "role_display", "avatar", "is_active",
            "branch", "created_at", "updated_at",
            "activity_count", "last_activity",
            "clients_count", "vehicles_count", "inspections_count", "sms_count",
        ]

    def get_activity_count(self, obj) -> int:
        return ActivityLog.objects.filter(user=obj).count()

    def get_last_activity(self, obj):
        log = ActivityLog.objects.filter(user=obj).first()
        return log.created_at if log else None

    def get_clients_count(self, obj) -> int:
        return obj.created_clients.filter(deleted_at__isnull=True).count()

    def get_vehicles_count(self, obj) -> int:
        return obj.created_vehicles.filter(deleted_at__isnull=True).count()

    def get_inspections_count(self, obj) -> int:
        return obj.inspected.filter(deleted_at__isnull=True).count()

    def get_sms_count(self, obj) -> int:
        return obj.created_reminders.filter(
            trigger_type="manual", deleted_at__isnull=True
        ).count()


class EmployeeWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["full_name", "phone", "role", "is_active", "branch", "password"]

    def validate_password(self, value: str) -> str:
        return value

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        actor = getattr(request, "user", None) if request else None
        instance = self.instance

        if actor is None:
            return attrs

        # Hech kim o'z rolini o'zi oshira/tushira olmaydi (bu endpoint orqali umuman
        # o'zgartira olmasligi kerak — rol o'zgarishi faqat boshqa admin tomonidan).
        if instance is not None and instance.pk == actor.pk and "role" in attrs and attrs["role"] != instance.role:
            raise serializers.ValidationError(
                {"role": "O'zingizning rolingizni o'zgartira olmaysiz."}
            )

        if actor.role == User.Role.BRANCH_ADMIN:
            current_role = instance.role if instance is not None else User.Role.OPERATOR
            target_role = attrs.get("role", current_role)

            # branch_admin faqat operator yarata/tahrirlay oladi
            if target_role != User.Role.OPERATOR:
                raise serializers.ValidationError(
                    {"role": "Filial admini faqat 'operator' rolidagi xodim yarata yoki tahrirlay oladi."}
                )
            if instance is not None and instance.role != User.Role.OPERATOR:
                raise serializers.ValidationError(
                    {"role": "Bu xodimni tahrirlash huquqingiz yo'q."}
                )

            # branch_admin xodim yaratganda/tahrirlaganda filial har doim o'zinikiga majburlanadi
            attrs["branch"] = actor.branch
        elif actor.role != User.Role.SUPER_ADMIN:
            # operator umuman xodimlarni CRUD qila olmaydi (view permission bilan ham bloklangan),
            # lekin serializer darajasida ham himoya qo'yamiz.
            raise serializers.ValidationError(
                {"detail": "Xodimlarni boshqarish huquqingiz yo'q."}
            )

        return attrs

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
    branch = BranchMinimalSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "full_name", "phone",
            "role", "role_display", "avatar", "branch",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "role", "role_display", "created_at", "updated_at"]


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone", "avatar"]

    def validate_full_name(self, value: str) -> str:
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Ism kamida 2 ta belgidan iborat bo'lishi kerak.")
        return value.strip()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, min_length=1)
    new_password = serializers.CharField(write_only=True, min_length=4)
    confirm_password = serializers.CharField(write_only=True, min_length=4)

    def validate_new_password(self, value: str) -> str:
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Parollar mos kelmadi."})
        return attrs
