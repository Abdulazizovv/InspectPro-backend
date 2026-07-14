from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class AuthService:
    @staticmethod
    def login(phone: str, password: str) -> dict:
        user = authenticate(phone=phone, password=password)
        if not user:
            raise AuthenticationFailed("Telefon raqam yoki parol noto'g'ri.")
        if not user.is_active:
            raise AuthenticationFailed("Foydalanuvchi faol emas.")
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user,
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            raise ValidationError({"refresh": "Noto'g'ri yoki eskirgan token."})

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> None:
        if not user.check_password(old_password):
            raise ValidationError({"old_password": "Eski parol noto'g'ri."})
        if old_password == new_password:
            raise ValidationError({"new_password": "Yangi parol eski parol bilan bir xil bo'lmasligi kerak."})
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
