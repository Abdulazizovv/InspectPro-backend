from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.accounts.permissions import IsSuperAdmin, IsAnyAdmin
from .filters import BranchFilter
from .models import Branch
from .serializers import BranchSerializer


@extend_schema_view(
    list=extend_schema(summary="Filiallar ro'yxati", tags=["Branches"]),
    retrieve=extend_schema(summary="Filial ma'lumotlari", tags=["Branches"]),
    create=extend_schema(summary="Yangi filial qo'shish", tags=["Branches"]),
    update=extend_schema(summary="Filialni yangilash", tags=["Branches"]),
    partial_update=extend_schema(summary="Filialni qisman yangilash", tags=["Branches"]),
    destroy=extend_schema(summary="Filialni o'chirish (soft)", tags=["Branches"]),
)
class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BranchFilter
    search_fields = ["name", "code", "address", "phone"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAnyAdmin()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        return Branch.objects.active().annotate(
            _employees_count=Count(
                "users",
                filter=Q(users__is_active=True),
                distinct=True,
            ),
            _clients_count=Count(
                "clients",
                filter=Q(clients__deleted_at__isnull=True),
                distinct=True,
            ),
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Filialni arxivlash/faollashtirish", tags=["Branches"])
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        branch = self.get_object()
        branch.is_active = not branch.is_active
        branch.save(update_fields=["is_active"])
        status_text = "arxivlandi" if not branch.is_active else "faollashtirildi"
        return Response({"detail": f"Filial {status_text}", "is_active": branch.is_active})
