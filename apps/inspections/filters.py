import django_filters
from .models import Inspection


class InspectionFilter(django_filters.FilterSet):
    vehicle = django_filters.UUIDFilter(field_name="vehicle__id")
    status = django_filters.ChoiceFilter(choices=Inspection.Status.choices)
    inspection_type = django_filters.ChoiceFilter(choices=Inspection.InspectionType.choices)
    inspector = django_filters.UUIDFilter(field_name="inspector__id")
    date_from = django_filters.DateFilter(field_name="inspection_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="inspection_date", lookup_expr="lte")
    today = django_filters.BooleanFilter(method="filter_today")

    class Meta:
        model = Inspection
        fields = ["vehicle", "status", "inspection_type", "inspector", "date_from", "date_to"]

    def filter_today(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(inspection_date=timezone.localdate())
        return queryset
