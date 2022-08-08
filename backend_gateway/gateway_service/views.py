import requests

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.views import APIView


class ServiceUrl:
    SESSION = 'http://127.0.0.1:8082'
    PUBLICATION = 'http://127.0.0.1:8083'
    SUBSCRIPTION = 'http://127.0.0.1:8084'
    STATISTICS = 'http://127.0.0.1:8085'


def redirect_get(request: Request, url: str) -> HttpResponse:
    params = request.query_params.copy()
    params['page'] = params.get('page', 1)
    params['page_size'] = params.get('page_size', 999999)
    res = requests.get(url, params)
    return HttpResponse(content=res.content, status=res.status_code, content_type=res.headers['content-type'])


def redirect_post(request: Request, url: str) -> HttpResponse:
    res = requests.post(url, data=request.data)
    return HttpResponse(content=res.content, status=res.status_code, content_type=res.headers['content-type'])


class Users(APIView):
    @staticmethod
    def get(request: Request) -> HttpResponse:
        return redirect_get(request, ServiceUrl.SESSION + '/api/v1/users/')

    @staticmethod
    def post(request: Request) -> HttpResponse:
        return redirect_post(request, ServiceUrl.SESSION + '/api/v1/users/')


@api_view(['POST'])
def user_by_token(request: Request) -> HttpResponse:
    return redirect_post(request, ServiceUrl.SESSION + '/api/v1/user-by-token/')


@api_view(['GET'])
def tags(request: Request) -> HttpResponse:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/tags/')


@api_view(['GET'])
def votes(request: Request) -> HttpResponse:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/votes/')


@api_view(['GET'])
def publications(request: Request) -> HttpResponse:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/publications/')


@api_view(['GET'])
def comments(request: Request) -> HttpResponse:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/comments/')
