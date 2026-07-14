from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from .filters import PaymentFilter
from .models import Payment
from .serializers import PaymentDetailSerializer, PaymentListSerializer, PaymentWriteSerializer


@extend_schema_view(
    list=extend_schema(summary="To'lovlar ro'yxati", tags=["Payments"]),
    retrieve=extend_schema(summary="To'lov ma'lumotlari", tags=["Payments"]),
    create=extend_schema(summary="Yangi to'lov qo'shish", tags=["Payments"]),
    update=extend_schema(summary="To'lovni yangilash", tags=["Payments"]),
    partial_update=extend_schema(summary="To'lovni qisman yangilash", tags=["Payments"]),
    destroy=extend_schema(summary="To'lovni o'chirish (soft)", tags=["Payments"]),
)
class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = ["client__full_name", "client__phone", "vehicle__plate_number", "notes"]
    ordering_fields = ["amount", "payment_date", "status", "created_at"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        return Payment.objects.active().select_related(
            "client", "vehicle", "inspection", "created_by"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        if self.action in ("create", "update", "partial_update"):
            return PaymentWriteSerializer
        return PaymentDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
