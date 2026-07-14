from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth


class DashboardService:
    @staticmethod
    def get_stats() -> dict:
        return {
            "overview": DashboardService._get_overview(),
            "monthly_inspections": DashboardService._monthly_inspections(),
            "monthly_revenue": DashboardService._monthly_revenue(),
            "expiring_soon": DashboardService._expiring_soon(),
            "recent_activities": [],
        }

    @staticmethod
    def _get_overview() -> dict:
        from django.utils import timezone
        from apps.accounts.models import User
        from apps.clients.models import Client
        from apps.vehicles.models import Vehicle
        from apps.inspections.models import Inspection

        today = timezone.localdate()
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        monthly_revenue = (
            Inspection.objects.active()
            .filter(inspection_date__gte=first_of_month, amount__isnull=False)
            .aggregate(total=Sum("amount"))["total"] or 0
        )
        last_month_revenue = (
            Inspection.objects.active()
            .filter(
                inspection_date__gte=last_month_start,
                inspection_date__lte=last_month_end,
                amount__isnull=False,
            )
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        this_month_inspections = Inspection.objects.active().filter(
            inspection_date__gte=first_of_month
        ).count()
        last_month_inspections = Inspection.objects.active().filter(
            inspection_date__gte=last_month_start,
            inspection_date__lte=last_month_end,
        ).count()

        return {
            "total_clients": Client.objects.active().filter(is_active=True).count(),
            "total_vehicles": Vehicle.objects.active().filter(is_active=True).count(),
            "today_inspections": Inspection.objects.active().filter(inspection_date=today).count(),
            "upcoming_expirations": Vehicle.objects.active().filter(
                expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)
            ).count(),
            "expires_15_days": Vehicle.objects.active().filter(
                expiry_date__gte=today, expiry_date__lte=today + timedelta(days=15)
            ).count(),
            "expired_vehicles": Vehicle.objects.active().filter(
                expiry_date__lt=today, expiry_date__isnull=False
            ).count(),
            "monthly_revenue": str(monthly_revenue),
            "total_employees": User.objects.filter(is_active=True).count(),
            "new_vehicles_this_month": Vehicle.objects.active().filter(
                created_at__date__gte=first_of_month
            ).count(),
            "inspections_change": this_month_inspections - last_month_inspections,
            "revenue_change": str(float(monthly_revenue) - float(last_month_revenue)),
        }

    @staticmethod
    def _monthly_inspections() -> list[dict]:
        from apps.inspections.models import Inspection

        today = date.today()
        twelve_months_ago = date(today.year - 1, today.month, 1)

        db_data = (
            Inspection.objects.active()
            .filter(inspection_date__gte=twelve_months_ago)
            .annotate(month=TruncMonth("inspection_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        db_map = {row["month"].strftime("%Y-%m"): row["count"] for row in db_data}

        result = []
        for i in range(11, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            key = f"{y}-{m:02d}"
            result.append({
                "month": date(y, m, 1).strftime("%b"),
                "year": y,
                "count": db_map.get(key, 0),
            })
        return result

    @staticmethod
    def _expiring_soon() -> list[dict]:
        from django.utils import timezone
        from apps.vehicles.models import Vehicle
        from apps.reminders.models import SmsReminder

        today = timezone.localdate()
        cutoff = today + timedelta(days=15)

        # Texnik ko'rik muddati yaqinlashayotganlar
        tech_vehicles = (
            Vehicle.objects.active()
            .filter(expiry_date__gte=today, expiry_date__lte=cutoff, is_active=True)
            .select_related("client")
            .order_by("expiry_date")
        )

        # Gaz ballon muddati yaqinlashayotganlar
        gas_vehicles = (
            Vehicle.objects.active()
            .filter(
                gas_cylinder_expiry_date__gte=today,
                gas_cylinder_expiry_date__lte=cutoff,
                engine_type__in=["metan", "propan"],
                is_active=True,
            )
            .select_related("client")
            .order_by("gas_cylinder_expiry_date")
        )

        result = []

        for v in tech_vehicles:
            reminder = SmsReminder.objects.filter(
                vehicle=v,
                inspection_type="technical",
                deleted_at__isnull=True,
            ).order_by("-created_at").first()

            result.append({
                "vehicle_id": str(v.id),
                "plate_number": v.plate_number,
                "client_name": v.client.full_name if v.client else "",
                "client_phone": v.client.phone if v.client else "",
                "expiry_date": v.expiry_date.strftime("%Y-%m-%d"),
                "gas_cylinder_expiry_date": None,
                "days_left": (v.expiry_date - today).days,
                "inspection_type": "technical",
                "sms_status": reminder.status if reminder else None,
            })

        for v in gas_vehicles:
            reminder = SmsReminder.objects.filter(
                vehicle=v,
                inspection_type="gas_cylinder",
                deleted_at__isnull=True,
            ).order_by("-created_at").first()

            result.append({
                "vehicle_id": str(v.id),
                "plate_number": v.plate_number,
                "client_name": v.client.full_name if v.client else "",
                "client_phone": v.client.phone if v.client else "",
                "expiry_date": v.expiry_date.strftime("%Y-%m-%d") if v.expiry_date else None,
                "gas_cylinder_expiry_date": v.gas_cylinder_expiry_date.strftime("%Y-%m-%d"),
                "days_left": (v.gas_cylinder_expiry_date - today).days,
                "inspection_type": "gas_cylinder",
                "sms_status": reminder.status if reminder else None,
            })

        result.sort(key=lambda x: x["days_left"])
        return result

    @staticmethod
    def _monthly_revenue() -> list[dict]:
        from apps.inspections.models import Inspection

        today = date.today()
        twelve_months_ago = date(today.year - 1, today.month, 1)

        db_data = (
            Inspection.objects.active()
            .filter(inspection_date__gte=twelve_months_ago, amount__isnull=False)
            .annotate(month=TruncMonth("inspection_date"))
            .values("month")
            .annotate(amount=Sum("amount"))
            .order_by("month")
        )
        db_map = {row["month"].strftime("%Y-%m"): float(row["amount"]) for row in db_data}

        result = []
        for i in range(11, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            key = f"{y}-{m:02d}"
            result.append({
                "month": date(y, m, 1).strftime("%b"),
                "year": y,
                "amount": db_map.get(key, 0),
            })
        return result


class ReportsService:
    @staticmethod
    def get_report(date_from, date_to) -> dict:
        return {
            "summary": ReportsService._summary(date_from, date_to),
            "inspections_by_status": ReportsService._inspections_by_status(date_from, date_to),
            "inspections_by_type": ReportsService._inspections_by_type(date_from, date_to),
            "revenue_by_month": ReportsService._revenue_by_month(date_from, date_to),
            "top_inspectors": ReportsService._top_inspectors(date_from, date_to),
            "expiry_report": ReportsService._expiry_report(),
        }

    @staticmethod
    def _date_filter(qs, field, date_from, date_to):
        if date_from:
            qs = qs.filter(**{f"{field}__gte": date_from})
        if date_to:
            qs = qs.filter(**{f"{field}__lte": date_to})
        return qs

    @staticmethod
    def _summary(date_from, date_to) -> dict:
        from apps.inspections.models import Inspection
        qs = ReportsService._date_filter(
            Inspection.objects.active(), "inspection_date", date_from, date_to
        )
        total_revenue = qs.filter(amount__isnull=False).aggregate(t=Sum("amount"))["t"] or Decimal(0)
        return {
            "total_inspections": qs.count(),
            "passed_inspections": qs.filter(status=Inspection.Status.PASSED).count(),
            "failed_inspections": qs.filter(status=Inspection.Status.FAILED).count(),
            "scheduled_inspections": qs.filter(status=Inspection.Status.SCHEDULED).count(),
            "total_revenue": float(total_revenue),
            "technical_count": qs.filter(inspection_type=Inspection.InspectionType.TECHNICAL).count(),
            "gas_cylinder_count": qs.filter(inspection_type=Inspection.InspectionType.GAS_CYLINDER).count(),
        }

    @staticmethod
    def _inspections_by_status(date_from, date_to) -> list[dict]:
        from apps.inspections.models import Inspection
        qs = ReportsService._date_filter(
            Inspection.objects.active(), "inspection_date", date_from, date_to
        )
        rows = qs.values("status").annotate(count=Count("id")).order_by("status")
        labels = {"scheduled": "Rejalashtirilgan", "passed": "O'tdi", "failed": "O'tmadi"}
        return [{"status": r["status"], "status_display": labels.get(r["status"], r["status"]), "count": r["count"]} for r in rows]

    @staticmethod
    def _inspections_by_type(date_from, date_to) -> list[dict]:
        from apps.inspections.models import Inspection
        qs = ReportsService._date_filter(
            Inspection.objects.active(), "inspection_date", date_from, date_to
        )
        rows = qs.values("inspection_type").annotate(count=Count("id"), revenue=Sum("amount")).order_by("inspection_type")
        labels = {"technical": "Texnik ko'rik", "gas_cylinder": "Gaz ballon akt"}
        return [
            {
                "inspection_type": r["inspection_type"],
                "label": labels.get(r["inspection_type"], r["inspection_type"]),
                "count": r["count"],
                "revenue": float(r["revenue"] or 0),
            }
            for r in rows
        ]

    @staticmethod
    def _revenue_by_month(date_from, date_to) -> list[dict]:
        from apps.inspections.models import Inspection
        qs = ReportsService._date_filter(
            Inspection.objects.active().filter(amount__isnull=False),
            "inspection_date", date_from, date_to
        )
        rows = (
            qs.annotate(month=TruncMonth("inspection_date"))
            .values("month")
            .annotate(amount=Sum("amount"), count=Count("id"))
            .order_by("month")
        )
        return [
            {
                "month": row["month"].strftime("%Y-%m"),
                "month_display": row["month"].strftime("%b %Y"),
                "amount": float(row["amount"]),
                "count": row["count"],
            }
            for row in rows
        ]

    @staticmethod
    def _top_inspectors(date_from, date_to) -> list[dict]:
        from apps.inspections.models import Inspection
        qs = ReportsService._date_filter(
            Inspection.objects.active().filter(inspector__isnull=False),
            "inspection_date", date_from, date_to,
        )
        rows = qs.values("inspector__id", "inspector__full_name").annotate(
            total=Count("id"),
            passed=Count("id", filter=Q(status="passed")),
            failed=Count("id", filter=Q(status="failed")),
            revenue=Sum("amount"),
        ).order_by("-total")[:10]
        return [
            {
                "inspector_id": str(r["inspector__id"]),
                "inspector_name": r["inspector__full_name"],
                "total": r["total"],
                "passed": r["passed"],
                "failed": r["failed"],
                "revenue": float(r["revenue"] or 0),
            }
            for r in rows
        ]

    @staticmethod
    def _expiry_report() -> dict:
        from apps.vehicles.models import Vehicle
        today = date.today()
        return {
            "expired": Vehicle.objects.active().filter(expiry_date__lt=today, expiry_date__isnull=False, is_active=True).count(),
            "expires_7_days": Vehicle.objects.active().filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7), is_active=True).count(),
            "expires_30_days": Vehicle.objects.active().filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30), is_active=True).count(),
        }
