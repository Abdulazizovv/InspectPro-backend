from datetime import date

from rest_framework import serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsAnyAdmin
from .models import SiteSettings
from .serializers import DashboardStatsSerializer
from .services import DashboardService, ReportsService


class DashboardStatsView(APIView):
    permission_classes = [IsAnyAdmin]

    @extend_schema(
        responses={200: DashboardStatsSerializer},
        summary="Dashboard statistikasi",
        description="Umumiy ko'rsatkichlar, oylik grafiklar va so'nggi faoliyatlar.",
        tags=["Dashboard"],
    )
    def get(self, request):
        # Branch filter aniqlash
        user = request.user
        branch = None
        if user.role != "super_admin":
            branch = getattr(user, "branch", None)
        else:
            branch_id = request.query_params.get("branch")
            if branch_id:
                from apps.branches.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    pass
        stats = DashboardService.get_stats(branch=branch)
        return Response(DashboardStatsSerializer(stats).data)


class ReportsView(APIView):
    permission_classes = [IsAnyAdmin]

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

        user = request.user
        branch = None
        if user.role != "super_admin":
            branch = getattr(user, "branch", None)
        else:
            branch_id = request.query_params.get("branch")
            if branch_id:
                from apps.branches.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    pass

        return Response(ReportsService.get_report(date_from, date_to, branch=branch))


class SiteSettingsSerializer(drf_serializers.ModelSerializer):
    branch = drf_serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SiteSettings
        fields = [
            "inspection_price",
            "branch",
            "auto_sms_hour",
            "auto_sms_minute",
            "auto_sms_enabled",
        ]


class SiteSettingsView(APIView):
    permission_classes = [IsAnyAdmin]

    def _get_settings(self, request):
        user = request.user
        if user.role == "super_admin":
            branch_id = request.query_params.get("branch")
            if branch_id:
                from apps.branches.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id)
                    return SiteSettings.get_for_branch(branch)
                except Branch.DoesNotExist:
                    pass
            return SiteSettings.get()
        else:
            branch = getattr(user, "branch", None)
            if branch:
                return SiteSettings.get_for_branch(branch)
            return SiteSettings.get()

    def get(self, request):
        settings_obj = self._get_settings(request)
        return Response(SiteSettingsSerializer(settings_obj).data)

    def patch(self, request):
        settings_obj = self._get_settings(request)
        serializer = SiteSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
