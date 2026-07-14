from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

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
class InspectionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InspectionFilter
    search_fields = ["vehicle__plate_number", "vehicle__brand", "vehicle__model", "vehicle__client__full_name"]
    ordering_fields = ["inspection_date", "expiry_date", "status", "created_at"]
    ordering = ["-inspection_date"]

    def get_queryset(self):
        return Inspection.objects.active().select_related(
            "vehicle", "vehicle__client", "inspector", "created_by"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return InspectionListSerializer
        if self.action in ("create", "update", "partial_update"):
            return InspectionWriteSerializer
        return InspectionDetailSerializer

    def perform_create(self, serializer):
        InspectionService.create(
            validated_data=serializer.validated_data,
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        InspectionService.update(
            inspection=serializer.instance,
            validated_data=serializer.validated_data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
