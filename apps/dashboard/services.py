from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth, TruncDate


class DashboardService:
    @staticmethod
    def get_stats(branch=None) -> dict:
        bf = {"branch": branch} if branch else {}
        return {
            "overview": DashboardService._get_overview(bf),
            "monthly_inspections": DashboardService._monthly_inspections(bf),
            "monthly_revenue": DashboardService._monthly_revenue(bf),
            "expiring_soon": DashboardService._expiring_soon(bf),
            "recent_activities": [],
        }

    @staticmethod
    def _get_overview(bf: dict) -> dict:
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
            .filter(inspection_date__gte=first_of_month, amount__isnull=False, **bf)
            .aggregate(total=Sum("amount"))["total"] or 0
        )
        last_month_revenue = (
            Inspection.objects.active()
            .filter(
                inspection_date__gte=last_month_start,
                inspection_date__lte=last_month_end,
                amount__isnull=False,
                **bf,
            )
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        this_month_inspections = Inspection.objects.active().filter(
            inspection_date__gte=first_of_month, **bf
        ).count()
        last_month_inspections = Inspection.objects.active().filter(
            inspection_date__gte=last_month_start,
            inspection_date__lte=last_month_end,
            **bf,
        ).count()

        vbf = bf
        ubf = bf
        return {
            "total_clients": Client.objects.active().filter(is_active=True, **vbf).count(),
            "total_vehicles": Vehicle.objects.active().filter(is_active=True, **vbf).count(),
            "today_inspections": Inspection.objects.active().filter(inspection_date=today, **bf).count(),
            "upcoming_expirations": Vehicle.objects.active().filter(
                expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30), **vbf
            ).count(),
            "expires_15_days": Vehicle.objects.active().filter(
                expiry_date__gte=today, expiry_date__lte=today + timedelta(days=15), **vbf
            ).count(),
            "expired_vehicles": Vehicle.objects.active().filter(
                expiry_date__lt=today, expiry_date__isnull=False, **vbf
            ).count(),
            "monthly_revenue": str(monthly_revenue),
            "total_employees": User.objects.filter(is_active=True, **ubf).count(),
            "new_vehicles_this_month": Vehicle.objects.active().filter(
                created_at__date__gte=first_of_month, **vbf
            ).count(),
            "inspections_change": this_month_inspections - last_month_inspections,
            "revenue_change": str(float(monthly_revenue) - float(last_month_revenue)),
        }

    @staticmethod
    def _monthly_inspections(bf: dict) -> list[dict]:
        from apps.inspections.models import Inspection

        today = date.today()
        twelve_months_ago = date(today.year - 1, today.month, 1)

        db_data = (
            Inspection.objects.active()
            .filter(inspection_date__gte=twelve_months_ago, **bf)
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
    def _expiring_soon(bf: dict) -> list[dict]:
        from django.utils import timezone
        from apps.vehicles.models import Vehicle
        from apps.reminders.models import SmsReminder

        today = timezone.localdate()
        cutoff = today + timedelta(days=15)

        tech_vehicles = (
            Vehicle.objects.active()
            .filter(expiry_date__gte=today, expiry_date__lte=cutoff, is_active=True, **bf)
            .select_related("client")
            .order_by("expiry_date")
        )

        gas_vehicles = (
            Vehicle.objects.active()
            .filter(
                gas_cylinder_expiry_date__gte=today,
                gas_cylinder_expiry_date__lte=cutoff,
                engine_type__in=["metan", "propan"],
                is_active=True,
                **bf,
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
    def _monthly_revenue(bf: dict) -> list[dict]:
        from apps.inspections.models import Inspection

        today = date.today()
        twelve_months_ago = date(today.year - 1, today.month, 1)

        db_data = (
            Inspection.objects.active()
            .filter(inspection_date__gte=twelve_months_ago, amount__isnull=False, **bf)
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
    def get_report(date_from, date_to, branch=None) -> dict:
        bf = {"branch": branch} if branch else {}
        today = date.today()

        # Default: oxirgi 30 kun
        if not date_from:
            date_from = today - timedelta(days=30)
        if not date_to:
            date_to = today

        return {
            "summary": ReportsService._summary(date_from, date_to, bf),
            "inspections_by_type": ReportsService._inspections_by_type(date_from, date_to, bf),
            "daily_inspections": ReportsService._daily_inspections(date_from, date_to, bf),
            "daily_revenue": ReportsService._daily_revenue(date_from, date_to, bf),
            "by_inspector": ReportsService._by_inspector(date_from, date_to, bf),
            "expired_vehicles": ReportsService._expired_vehicles(bf),
            "expires_30_days_list": ReportsService._expires_30_days_list(bf),
        }

    @staticmethod
    def _date_filter(qs, field, date_from, date_to):
        if date_from:
            qs = qs.filter(**{f"{field}__gte": date_from})
        if date_to:
            qs = qs.filter(**{f"{field}__lte": date_to})
        return qs

    @staticmethod
    def _passed_qs(date_from, date_to, bf: dict):
        """Faqat 'passed' statusli ko'riklar"""
        from apps.inspections.models import Inspection
        qs = Inspection.objects.active().filter(status=Inspection.Status.PASSED, **bf)
        return ReportsService._date_filter(qs, "inspection_date", date_from, date_to)

    @staticmethod
    def _summary(date_from, date_to, bf: dict) -> dict:
        from apps.vehicles.models import Vehicle
        today = date.today()

        qs = ReportsService._passed_qs(date_from, date_to, bf)
        total_revenue = qs.filter(amount__isnull=False).aggregate(t=Sum("amount"))["t"] or Decimal(0)

        expired_count = Vehicle.objects.active().filter(
            expiry_date__lt=today, expiry_date__isnull=False, is_active=True, **bf
        ).count()

        expires_30 = Vehicle.objects.active().filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=30),
            is_active=True,
            **bf,
        ).count()

        return {
            "total_inspections": qs.count(),
            "total_revenue": float(total_revenue),
            "expired_count": expired_count,
            "expires_30_days": expires_30,
        }

    @staticmethod
    def _inspections_by_type(date_from, date_to, bf: dict) -> list[dict]:
        qs = ReportsService._passed_qs(date_from, date_to, bf)
        rows = (
            qs.values("inspection_type")
            .annotate(count=Count("id"), revenue=Sum("amount"))
            .order_by("inspection_type")
        )
        labels = {"technical": "Texnik ko'rik", "gas_cylinder": "Gaz ballon akt"}
        return [
            {
                "type": r["inspection_type"],
                "label": labels.get(r["inspection_type"], r["inspection_type"]),
                "count": r["count"],
                "revenue": float(r["revenue"] or 0),
            }
            for r in rows
        ]

    @staticmethod
    def _daily_inspections(date_from, date_to, bf: dict) -> list[dict]:
        qs = ReportsService._passed_qs(date_from, date_to, bf)
        rows = (
            qs.annotate(day=TruncDate("inspection_date"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        return [
            {"date": row["day"].strftime("%Y-%m-%d"), "count": row["count"]}
            for row in rows
        ]

    @staticmethod
    def _daily_revenue(date_from, date_to, bf: dict) -> list[dict]:
        qs = ReportsService._passed_qs(date_from, date_to, bf).filter(amount__isnull=False)
        rows = (
            qs.annotate(day=TruncDate("inspection_date"))
            .values("day")
            .annotate(amount=Sum("amount"))
            .order_by("day")
        )
        return [
            {"date": row["day"].strftime("%Y-%m-%d"), "amount": float(row["amount"] or 0)}
            for row in rows
        ]

    @staticmethod
    def _by_inspector(date_from, date_to, bf: dict) -> list[dict]:
        qs = ReportsService._passed_qs(date_from, date_to, bf).filter(inspector__isnull=False)
        rows = (
            qs.values("inspector__id", "inspector__full_name")
            .annotate(total=Count("id"), revenue=Sum("amount"))
            .order_by("-total")[:10]
        )
        return [
            {
                "inspector_id": str(r["inspector__id"]),
                "name": r["inspector__full_name"] or "",
                "total": r["total"],
                "revenue": float(r["revenue"] or 0),
            }
            for r in rows
        ]

    @staticmethod
    def _expired_vehicles(bf: dict) -> list[dict]:
        from apps.vehicles.models import Vehicle
        today = date.today()
        vehicles = (
            Vehicle.objects.active()
            .filter(expiry_date__lt=today, expiry_date__isnull=False, is_active=True, **bf)
            .select_related("client")
            .order_by("expiry_date")[:50]
        )
        result = []
        for v in vehicles:
            result.append({
                "plate": v.plate_number,
                "client": v.client.full_name if v.client else "",
                "phone": v.client.phone if v.client else "",
                "expiry_date": v.expiry_date.strftime("%Y-%m-%d"),
                "days_overdue": (today - v.expiry_date).days,
            })
        return result

    @staticmethod
    def _expires_30_days_list(bf: dict) -> list[dict]:
        from apps.vehicles.models import Vehicle
        today = date.today()
        vehicles = (
            Vehicle.objects.active()
            .filter(
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=30),
                is_active=True,
                **bf,
            )
            .select_related("client")
            .order_by("expiry_date")[:50]
        )
        result = []
        for v in vehicles:
            result.append({
                "plate": v.plate_number,
                "client": v.client.full_name if v.client else "",
                "phone": v.client.phone if v.client else "",
                "expiry_date": v.expiry_date.strftime("%Y-%m-%d"),
                "days_left": (v.expiry_date - today).days,
            })
        return result
