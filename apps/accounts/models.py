import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

from apps.common.models import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Email majburiy.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPER_ADMIN  = "super_admin",  "Super Admin"
        BRANCH_ADMIN = "branch_admin", "Filial Admini"
        OPERATOR     = "operator",     "Operator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Telefon")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR,
        verbose_name="Rol",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name="Avatar",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Filial",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan")

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name", "email"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"

    @property
    def is_super_admin(self) -> bool:
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_branch_admin(self) -> bool:
        return self.role == self.Role.BRANCH_ADMIN

    @property
    def is_operator(self) -> bool:
        return self.role == self.Role.OPERATOR

    @property
    def is_admin(self) -> bool:
        """Qulaylik uchun: super_admin yoki branch_admin."""
        return self.role in [self.Role.SUPER_ADMIN, self.Role.BRANCH_ADMIN]


class ActivityLog(BaseModel):
    class Action(models.TextChoices):
        VEHICLE_CREATED    = "vehicle_created",    "Avtomobil qo'shdi"
        VEHICLE_UPDATED    = "vehicle_updated",    "Avtomobil ma'lumotini o'zgartirdi"
        VEHICLE_DELETED    = "vehicle_deleted",    "Avtomobilni o'chirdi"
        CLIENT_CREATED     = "client_created",     "Mijoz qo'shdi"
        CLIENT_UPDATED     = "client_updated",     "Mijoz ma'lumotini o'zgartirdi"
        CLIENT_DELETED     = "client_deleted",     "Mijozni o'chirdi"
        INSPECTION_CREATED = "inspection_created", "Ko'rik qo'shdi"
        INSPECTION_UPDATED = "inspection_updated", "Ko'rik ma'lumotini o'zgartirdi"
        SMS_SENT_MANUAL    = "sms_sent_manual",    "Qo'lda SMS jo'natdi"
        LOGIN              = "login",              "Tizimga kirdi"
        LOGOUT             = "logout",             "Tizimdan chiqdi"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="activities"
    )
    branch = models.ForeignKey(
        "branches.Branch", on_delete=models.PROTECT, null=True, blank=True
    )
    action = models.CharField(max_length=50, choices=Action.choices)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "accounts_activitylog"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["branch", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.get_action_display()} ({self.created_at:%Y-%m-%d})"
