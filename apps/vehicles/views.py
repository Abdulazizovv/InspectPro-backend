from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.common.mixins import BranchScopedQuerysetMixin
from apps.common.activity import log_activity
from apps.accounts.models import ActivityLog
from .filters import VehicleFilter
from .models import Vehicle
from .serializers import VehicleDetailSerializer, VehicleListSerializer, VehicleWriteSerializer


@extend_schema_view(
    list=extend_schema(summary="Avtomobillar ro'yxati", tags=["Vehicles"]),
    retrieve=extend_schema(summary="Avtomobil ma'lumotlari", tags=["Vehicles"]),
    create=extend_schema(summary="Yangi avtomobil qo'shish", tags=["Vehicles"]),
    update=extend_schema(summary="Avtomobilni yangilash", tags=["Vehicles"]),
    partial_update=extend_schema(summary="Avtomobilni qisman yangilash", tags=["Vehicles"]),
    destroy=extend_schema(summary="Avtomobilni o'chirish (soft)", tags=["Vehicles"]),
)
class VehicleViewSet(BranchScopedQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VehicleFilter
    search_fields = ["brand", "model", "plate_number", "vin", "client__full_name", "client__phone"]
    ordering_fields = ["brand", "model", "year", "plate_number", "expiry_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Vehicle.objects.active().select_related("client", "created_by", "branch")
        return self._apply_branch_filter(qs)

    def get_serializer_class(self):
        if self.action == "list":
            return VehicleListSerializer
        if self.action in ("create", "update", "partial_update"):
            return VehicleWriteSerializer
        return VehicleDetailSerializer

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
        log_activity(user, ActivityLog.Action.VEHICLE_CREATED, instance, self.request)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, ActivityLog.Action.VEHICLE_UPDATED, instance, self.request)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        log_activity(request.user, ActivityLog.Action.VEHICLE_DELETED, instance, request)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="check-plate")
    def check_plate(self, request):
        plate = request.query_params.get("plate", "").strip().upper()
        if not plate:
            return Response({"exists": False, "vehicle_id": None})
        # Faqat o'z filialida tekshirish
        user = request.user
        qs = Vehicle.objects.active().filter(plate_number__iexact=plate)
        if user.role != "super_admin" and user.branch:
            qs = qs.filter(branch=user.branch)
        vehicle = qs.first()
        if vehicle:
            return Response({
                "exists": True,
                "vehicle_id": str(vehicle.id),
                "plate_number": vehicle.plate_number,
                "brand": vehicle.brand,
                "model": vehicle.model,
            })
        return Response({"exists": False, "vehicle_id": None})

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        """
        Boshqa filialdagi mashina ma'lumotlarini lookup qilish.
        GET /api/v1/vehicles/lookup/?plate=<raqam>
        Yangi mashina qo'shishda avtomatik to'ldirish uchun.
        """
        plate = request.query_params.get("plate", "").strip().upper()
        if not plate:
            return Response({"found": False})

        # Barcha filiallarda qidirish (faqat authenticated user)
        vehicle = Vehicle.objects.active().filter(plate_number__iexact=plate).first()
        if not vehicle:
            return Response({"found": False})

        user = request.user
        is_same_branch = user.branch and str(vehicle.branch_id) == str(user.branch_id) if user.branch else False

        return Response({
            "found": True,
            "is_same_branch": is_same_branch,
            "branch_name": vehicle.branch.name if vehicle.branch else None,
            "vehicle_id": str(vehicle.id),
            "plate_number": vehicle.plate_number,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "year": vehicle.year,
            "color": vehicle.color,
            "vin": vehicle.vin,
            "engine_type": vehicle.engine_type,
        })
