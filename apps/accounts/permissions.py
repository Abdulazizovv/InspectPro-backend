from rest_framework.permissions import BasePermission

from .models import User


class IsSuperAdmin(BasePermission):
    """Faqat super_admin roli uchun."""
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.SUPER_ADMIN
        )


class IsBranchAdmin(BasePermission):
    """Faqat branch_admin roli uchun."""
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.BRANCH_ADMIN
        )


class IsAnyAdmin(BasePermission):
    """super_admin yoki branch_admin — ikkalasi uchun."""
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in [User.Role.SUPER_ADMIN, User.Role.BRANCH_ADMIN]
        )


class IsOperator(BasePermission):
    """Faqat operator roli uchun."""
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.OPERATOR
        )


class IsAnyRole(BasePermission):
    """Barcha autentifikatsiyalangan foydalanuvchilar uchun (operator + branch_admin + super_admin)."""
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)


# Qulaylik uchun alias (eski kod bilan muvofiqlik)
IsAdminOrManager = IsAnyAdmin
