from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample

from apps.common.mixins import BranchScopedQuerysetMixin
from apps.common.activity import log_activity
from .models import User, ActivityLog
from .permissions import IsAnyAdmin
from .serializers import (
    LoginSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    EmployeeWriteSerializer,
    ActivityLogSerializer,
)
from .services import AuthService


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Access va refresh tokenlar qaytariladi."),
            401: OpenApiResponse(description="Noto'g'ri email yoki parol."),
        },
        summary="Login",
        description="Email va parol orqali tizimga kirish. Access va refresh tokenlarni qaytaradi.",
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Login example",
                value={"phone": "+998901111111", "password": "admin123"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthService.login(
            phone=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
        )
        log_activity(result["user"], ActivityLog.Action.LOGIN, request=request)
        return Response(
            {
                "access": result["access"],
                "refresh": result["refresh"],
                "user": UserProfileSerializer(result["user"], context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}, "required": ["refresh"]}},
        responses={204: None, 400: OpenApiResponse(description="Noto'g'ri token.")},
        summary="Logout",
        tags=["Auth"],
    )
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "Refresh token kerak."}, status=status.HTTP_400_BAD_REQUEST)
        log_activity(request.user, ActivityLog.Action.LOGOUT, request=request)
        AuthService.logout(refresh)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        summary="Profilni ko'rish",
        tags=["Auth"],
    )
    def get(self, request):
        return Response(
            UserProfileSerializer(request.user, context={"request": request}).data
        )

    @extend_schema(
        request=UpdateProfileSerializer,
        responses={200: UserProfileSerializer},
        summary="Profilni yangilash",
        tags=["Auth"],
    )
    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            UserProfileSerializer(request.user, context={"request": request}).data
        )


@extend_schema_view(
    list=extend_schema(summary="Xodimlar ro'yxati", tags=["Employees"]),
    retrieve=extend_schema(summary="Xodim ma'lumotlari", tags=["Employees"]),
    create=extend_schema(summary="Yangi xodim qo'shish", tags=["Employees"]),
    update=extend_schema(summary="Xodimni yangilash", tags=["Employees"]),
    partial_update=extend_schema(summary="Xodimni qisman yangilash", tags=["Employees"]),
    destroy=extend_schema(summary="Xodimni o'chirish (deactivate)", tags=["Employees"]),
)
class EmployeeViewSet(BranchScopedQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAnyAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["full_name", "email", "phone"]
    ordering_fields = ["full_name", "role", "created_at", "is_active"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = User.objects.annotate(inspection_count=Count("inspected")).select_related("branch")
        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() == "true"))
        return self._apply_branch_filter(qs)

    def get_serializer_class(self):
        if self.action == "list":
            return EmployeeListSerializer
        if self.action in ("create", "update", "partial_update"):
            return EmployeeWriteSerializer
        return EmployeeDetailSerializer

    def perform_create(self, serializer):
        # User modelida created_by yo'q, faqat branch assign qilinadi
        # password handling EmployeeWriteSerializer.create() da amalga oshiriladi
        user = self.request.user
        branch = getattr(user, "branch", None)
        if user.role == "super_admin":
            branch_id = self.request.data.get("branch") or self.request.query_params.get("branch")
            if branch_id:
                from apps.branches.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    pass
        serializer.save(branch=branch)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response(
                {"detail": "O'zingizni o'chira olmaysiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Xodim faoliyat tarixi", tags=["Employees"])
    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        employee = self.get_object()
        logs = ActivityLog.objects.filter(user=employee).order_by("-created_at")
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = ActivityLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Admin xodim parolini o'zgartiradi", tags=["Employees"])
    @action(detail=True, methods=["post"], url_path="set-password", permission_classes=[IsAnyAdmin])
    def set_password(self, request, pk=None):
        employee = self.get_object()
        new_password = request.data.get("new_password", "")
        if len(new_password) < 4:
            return Response(
                {"detail": "Parol kamida 4 ta belgi bo'lishi kerak"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        employee.set_password(new_password)
        employee.save()
        return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi"})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Parol muvaffaqiyatli o'zgartirildi."),
            400: OpenApiResponse(description="Validatsiya xatosi."),
        },
        summary="Parolni o'zgartirish",
        tags=["Auth"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.change_password(
            request.user,
            serializer.validated_data["old_password"],
            serializer.validated_data["new_password"],
        )
        return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi."})
