import django_filters
from .models import Client


class ClientFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    phone = django_filters.CharFilter(lookup_expr="icontains")
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Client
        fields = ["is_active", "phone", "created_after", "created_before"]
