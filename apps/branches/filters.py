import django_filters

from .models import Branch


class BranchFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Branch
        fields = ["is_active"]
