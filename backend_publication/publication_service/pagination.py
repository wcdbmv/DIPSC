from collections import OrderedDict

from rest_framework import pagination
from rest_framework.response import Response


class Pagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('items_count', self.page.paginator.count),
            ('num_pages', self.page.paginator.num_pages),
            ('next_page_number', self.page.next_page_number() if self.page.has_next() else None),
            ('current_page_number', self.page.number),
            ('previous_page_number', self.page.previous_page_number() if self.page.has_previous() else None),
            ('items', data),
        ]))
