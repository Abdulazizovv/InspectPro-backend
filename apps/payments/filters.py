import django_filters
from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    client = django_filters.UUIDFilter(field_name="client__id")
    vehicle = django_filters.UUIDFilter(field_name="vehicle__id")
    status = django_filters.ChoiceFilter(choices=Payment.Status.choices)
    payment_method = django_filters.ChoiceFilter(choices=Payment.PaymentMethod.choices)
    date_from = django_filters.DateFilter(field_name="payment_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="payment_date", lookup_expr="lte")
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")

    class Meta:
        model = Payment
        fields = ["client", "vehicle", "status", "payment_method", "date_from", "date_to"]
