from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

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
class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClientFilter
    search_fields = ["full_name", "phone", "passport"]
    ordering_fields = ["full_name", "phone", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Client.objects.active()

    def get_serializer_class(self):
        if self.action == "list":
            return ClientListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ClientWriteSerializer
        return ClientDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()  # soft delete (BaseModel)
        return Response(status=status.HTTP_204_NO_CONTENT)
