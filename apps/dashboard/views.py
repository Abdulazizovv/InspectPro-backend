from datetime import date

from rest_framework import serializers as drf_serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import SiteSettings
from .serializers import DashboardStatsSerializer
from .services import DashboardService, ReportsService


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DashboardStatsSerializer},
        summary="Dashboard statistikasi",
        description="Umumiy ko'rsatkichlar, oylik grafiklar va so'nggi faoliyatlar.",
        tags=["Dashboard"],
    )
    def get(self, request):
        stats = DashboardService.get_stats()
        return Response(DashboardStatsSerializer(stats).data)


class ReportsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Hisobot ma'lumotlari",
        tags=["Reports"],
    )
    def get(self, request):
        def _parse_date(key: str) -> date | None:
            val = request.query_params.get(key)
            if not val:
                return None
            try:
                return date.fromisoformat(val)
            except ValueError:
                return None

        date_from = _parse_date("date_from")
        date_to = _parse_date("date_to")
        return Response(ReportsService.get_report(date_from, date_to))


class SiteSettingsSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = ["inspection_price"]


class SiteSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings = SiteSettings.get()
        return Response(SiteSettingsSerializer(settings).data)

    def patch(self, request):
        settings = SiteSettings.get()
        serializer = SiteSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
