import requests

from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class ServiceUrl:
    SESSION = 'http://127.0.0.1:8082'
    PUBLICATION = 'http://127.0.0.1:8083'
    SUBSCRIPTION = 'http://127.0.0.1:8084'
    STATISTICS = 'http://127.0.0.1:8085'


def redirect_get(request: Request, url: str) -> Response:
    params = request.query_params.copy()
    params['page'] = params.get('page', 1)
    params['page_size'] = params.get('page_size', 999999)
    res = requests.get(url, params)
    return Response(data=res.content, status=res.status_code)


def redirect_post(request: Request, url: str) -> Response:
    res = requests.post(url, data=request.data)
    return Response(data=res.content, status=res.status_code)


class Users(APIView):
    @staticmethod
    def get(request: Request) -> Response:
        return redirect_get(request, ServiceUrl.SESSION + '/api/v1/users/')

    @staticmethod
    def post(request: Request) -> Response:
        return redirect_post(request, ServiceUrl.SESSION + '/api/v1/users/')


@api_view(['GET'])
def tags(request: Request) -> Response:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/tags/')


@api_view(['GET'])
def votes(request: Request) -> Response:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/votes/')


@api_view(['GET'])
def publications(request: Request) -> Response:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/publications/')


@api_view(['GET'])
def comments(request: Request) -> Response:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/comments/')
