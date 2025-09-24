from rest_framework.pagination import LimitOffsetPagination


class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 100

    def paginate_queryset(self, queryset, request, view=None):
        queryset = queryset.order_by('-created_at')
        return super().paginate_queryset(queryset, request, view)
