import django_filters
from .models import Route


class RouteFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    priority = django_filters.NumberFilter(field_name='priority', lookup_expr='exact')
    origin = django_filters.CharFilter(field_name='origin', lookup_expr='icontains')
    destination = django_filters.CharFilter(field_name='destination', lookup_expr='icontains')
    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Route
        fields = ['status', 'priority', 'origin', 'destination']