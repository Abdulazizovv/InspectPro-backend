from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Faqat Admin roli uchun."""
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsAdminOrManager(BasePermission):
    """Admin yoki Manager roli uchun."""
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "manager")
        )


class IsAnyRole(BasePermission):
    """Barcha autentifikatsiyalangan foydalanuvchilar uchun (Admin, Manager, Operator)."""
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)
