from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

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
class VehicleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VehicleFilter
    search_fields = ["brand", "model", "plate_number", "vin", "client__full_name", "client__phone"]
    ordering_fields = ["brand", "model", "year", "plate_number", "expiry_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Vehicle.objects.active().select_related("client", "created_by")

    def get_serializer_class(self):
        if self.action == "list":
            return VehicleListSerializer
        if self.action in ("create", "update", "partial_update"):
            return VehicleWriteSerializer
        return VehicleDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="check-plate")
    def check_plate(self, request):
        plate = request.query_params.get("plate", "").strip().upper()
        if not plate:
            return Response({"exists": False, "vehicle_id": None})
        vehicle = Vehicle.objects.active().filter(plate_number__iexact=plate).first()
        if vehicle:
            return Response({
                "exists": True,
                "vehicle_id": str(vehicle.id),
                "plate_number": vehicle.plate_number,
                "brand": vehicle.brand,
                "model": vehicle.model,
            })
        return Response({"exists": False, "vehicle_id": None})
