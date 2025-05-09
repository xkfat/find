import django_filters
from .models import MissingPerson, GENDER, CASE_STATUS

class MissingPersonFilter(django_filters.FilterSet):
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

    class Meta:
        model = MissingPerson
        fields = [
          'gender',
          'status',
          'age_min',
          'age_max',
          'date_reported_start',
          'date_reported_end',
        ]
