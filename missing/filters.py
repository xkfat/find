import django_filters
from .models import MissingPerson, GENDER, CASE_STATUS
from django.db import models

class MissingPersonFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_by_name')
    location = django_filters.CharFilter(method='filter_by_location')
    name_or_location = django_filters.CharFilter(method='filter_by_name_or_location')

    gender = django_filters.ChoiceFilter(choices=GENDER)
    status = django_filters.ChoiceFilter(choices=CASE_STATUS)

    age_min = django_filters.NumberFilter(field_name='age', lookup_expr='gte')
    age_max = django_filters.NumberFilter(field_name='age', lookup_expr='lte')

    date_reported_start = django_filters.DateFilter(
        field_name='date_reported', lookup_expr='gte'
    )
    date_reported_end = django_filters.DateFilter(
        field_name='date_reported', lookup_expr='lte'
    )

    def filter_by_name(self, queryset, name, value):
        if value:
            return queryset.filter(
                models.Q(first_name__icontains=value) | 
                models.Q(last_name__icontains=value)
            )
        return queryset
    def filter_by_location(self, queryset, last_seen_location, value):
        if value:
            return queryset.filter(
                models.Q(last_seen_location__icontains=value) 
            )
        return queryset
    def filter_by_name_or_location(self, queryset, name, value):
        if value:
            return queryset.filter(
                models.Q(first_name__icontains=value) | 
                models.Q(last_name__icontains=value) |
                models.Q(last_seen_location__icontains=value)
            )
        return queryset

    class Meta:
        model = MissingPerson
        fields = [
          'name',
          'name_or_location',
          'location',
          'gender',
          'status',
          'age_min',
          'age_max',
          'date_reported_start',
          'date_reported_end',
        ]
