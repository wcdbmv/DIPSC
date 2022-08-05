import requests

from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.decorators import api_view


class ServiceUrl:
    SESSION = 'http://127.0.0.1:8082'
    PUBLICATION = 'http://127.0.0.1:8083'
    SUBSCRIPTION = 'http://127.0.0.1:8084'
    STATISTICS = 'http://127.0.0.1:8085'


def get(request: Request, url: str) -> HttpResponse:
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 999999)
    params = {'page': page, 'page_size': page_size}
    res = requests.get(url, params)
    return HttpResponse(content=res.content, status=res.status_code, headers=res.headers)


@api_view(['GET'])
def tags(request: Request) -> HttpResponse:
    return get(request, ServiceUrl.PUBLICATION + '/api/v1/tags/')


@api_view(['GET'])
def votes(request: Request) -> HttpResponse:
    return get(request, ServiceUrl.PUBLICATION + '/api/v1/votes/')


@api_view(['GET'])
def publications(request: Request) -> HttpResponse:
    return get(request, ServiceUrl.PUBLICATION + '/api/v1/publications/')


@api_view(['GET'])
def comments(request: Request) -> HttpResponse:
    return get(request, ServiceUrl.PUBLICATION + '/api/v1/comments/')
