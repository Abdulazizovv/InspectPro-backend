import django_filters
from datetime import timedelta
from django.utils import timezone

from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    client = django_filters.UUIDFilter(field_name="client__id")
    engine_type = django_filters.ChoiceFilter(choices=Vehicle.EngineType.choices)
    is_active = django_filters.BooleanFilter()
    plate_number = django_filters.CharFilter(lookup_expr="icontains")
    brand = django_filters.CharFilter(lookup_expr="icontains")
    year = django_filters.NumberFilter()
    year_min = django_filters.NumberFilter(field_name="year", lookup_expr="gte")
    year_max = django_filters.NumberFilter(field_name="year", lookup_expr="lte")

    # Muddati o'tgan avtomobillar
    expired = django_filters.BooleanFilter(method="filter_expired")
    # 30 kun ichida muddati tugaydigan
    upcoming = django_filters.BooleanFilter(method="filter_upcoming")

    class Meta:
        model = Vehicle
        fields = [
            "client", "engine_type", "is_active",
            "plate_number", "brand", "year",
        ]

    def filter_expired(self, queryset, name, value):
        today = timezone.localdate()
        if value:
            return queryset.filter(expiry_date__lt=today, expiry_date__isnull=False)
        return queryset.exclude(expiry_date__lt=today)

    def filter_upcoming(self, queryset, name, value):
        today = timezone.localdate()
        cutoff = today + timedelta(days=30)
        if value:
            return queryset.filter(expiry_date__gte=today, expiry_date__lte=cutoff)
        return queryset
