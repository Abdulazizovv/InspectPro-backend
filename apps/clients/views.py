from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.common.mixins import BranchScopedQuerysetMixin
from apps.common.activity import log_activity
from apps.accounts.models import ActivityLog
from .filters import ClientFilter
from .models import Client
from .serializers import ClientDetailSerializer, ClientListSerializer, ClientWriteSerializer


@extend_schema_view(
    list=extend_schema(summary="Mijozlar ro'yxati", tags=["Clients"]),
    retrieve=extend_schema(summary="Mijoz ma'lumotlari", tags=["Clients"]),
    create=extend_schema(summary="Yangi mijoz qo'shish", tags=["Clients"]),
    update=extend_schema(summary="Mijozni yangilash", tags=["Clients"]),
    partial_update=extend_schema(summary="Mijozni qisman yangilash", tags=["Clients"]),
    destroy=extend_schema(summary="Mijozni o'chirish (soft)", tags=["Clients"]),
)
class ClientViewSet(BranchScopedQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClientFilter
    search_fields = ["full_name", "phone", "passport"]
    ordering_fields = ["full_name", "phone", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Client.objects.active()
        return self._apply_branch_filter(qs)

    def get_serializer_class(self):
        if self.action == "list":
            return ClientListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ClientWriteSerializer
        return ClientDetailSerializer

    def perform_create(self, serializer):
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
        instance = serializer.save(branch=branch, created_by=user)
        log_activity(user, ActivityLog.Action.CLIENT_CREATED, instance, self.request)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, ActivityLog.Action.CLIENT_UPDATED, instance, self.request)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        log_activity(request.user, ActivityLog.Action.CLIENT_DELETED, instance, request)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
