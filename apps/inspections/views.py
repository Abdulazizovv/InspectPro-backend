from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.common.mixins import BranchScopedQuerysetMixin
from apps.common.activity import log_activity
from apps.accounts.models import ActivityLog
from .filters import InspectionFilter
from .models import Inspection
from .serializers import InspectionDetailSerializer, InspectionListSerializer, InspectionWriteSerializer
from .services import InspectionService


@extend_schema_view(
    list=extend_schema(summary="Ko'riklar ro'yxati", tags=["Inspections"]),
    retrieve=extend_schema(summary="Ko'rik ma'lumotlari", tags=["Inspections"]),
    create=extend_schema(summary="Yangi ko'rik qo'shish", tags=["Inspections"]),
    update=extend_schema(summary="Ko'rikni yangilash", tags=["Inspections"]),
    partial_update=extend_schema(summary="Ko'rikni qisman yangilash", tags=["Inspections"]),
    destroy=extend_schema(summary="Ko'rikni o'chirish (soft)", tags=["Inspections"]),
)
class InspectionViewSet(BranchScopedQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InspectionFilter
    search_fields = ["vehicle__plate_number", "vehicle__brand", "vehicle__model", "vehicle__client__full_name"]
    ordering_fields = ["inspection_date", "expiry_date", "status", "created_at"]
    ordering = ["-inspection_date"]

    def get_queryset(self):
        qs = Inspection.objects.active().select_related(
            "vehicle", "vehicle__client", "inspector", "created_by", "branch"
        )
        return self._apply_branch_filter(qs)

    def get_serializer_class(self):
        if self.action == "list":
            return InspectionListSerializer
        if self.action in ("create", "update", "partial_update"):
            return InspectionWriteSerializer
        return InspectionDetailSerializer

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
        instance = InspectionService.create(
            validated_data=serializer.validated_data,
            created_by=user,
            branch=branch,
        )
        log_activity(user, ActivityLog.Action.INSPECTION_CREATED, instance, self.request)

    def perform_update(self, serializer):
        instance = InspectionService.update(
            inspection=serializer.instance,
            validated_data=serializer.validated_data,
        )
        log_activity(self.request.user, ActivityLog.Action.INSPECTION_UPDATED, instance, self.request)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
