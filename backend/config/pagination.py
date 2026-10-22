from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """25 rows by default; clients that load a whole list may ask for up to 500 per page."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 500
