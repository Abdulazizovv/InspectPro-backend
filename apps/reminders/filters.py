import django_filters

from .models import SmsReminder


class SmsReminderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=SmsReminder.Status.choices)
    trigger_type = django_filters.ChoiceFilter(choices=SmsReminder.TriggerType.choices)
    date_from = django_filters.DateFilter(field_name="scheduled_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="scheduled_date", lookup_expr="lte")
    vehicle = django_filters.UUIDFilter(field_name="vehicle__id")

    class Meta:
        model = SmsReminder
        fields = ["status", "trigger_type", "date_from", "date_to", "vehicle"]
