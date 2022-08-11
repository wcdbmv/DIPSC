import json
import uuid

import requests

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.views import APIView


class ServiceUrl:
    SESSION = 'http://127.0.0.1:8082'
    PUBLICATION = 'http://127.0.0.1:8083'
    SUBSCRIPTION = 'http://127.0.0.1:8084'
    STATISTICS = 'http://127.0.0.1:8085'


def raw_request_no_query(url: str) -> requests.Response:
    return requests.get(url)


def raw_redirect_with_query(request: Request, url: str) -> requests.Response:
    return requests.get(url, request.query_params.copy())


def make_response(res: requests.Response) -> HttpResponse:
    return HttpResponse(content=res.content, status=res.status_code, content_type=res.headers['content-type'])


def redirect_get(request: Request, url: str) -> HttpResponse:
    return make_response(raw_redirect_with_query(request, url))


def redirect_post(request: Request, url: str) -> HttpResponse:
    return make_response(requests.post(url, data=request.data))


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


def replace_author(item):
    res = raw_request_no_query(f'{ServiceUrl.SESSION}/api/v1/users/{item["author_uid"]}/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)  # TODO
    item['author'] = res.json()
    del item['author_uid']


def replace_authors(items):
    for item in items:
        replace_author(item)


@api_view(['GET'])
def publications(request: Request) -> HttpResponse:
    res = raw_redirect_with_query(request, ServiceUrl.PUBLICATION + '/api/v1/publications/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    data = res.json()
    replace_authors(data['items'])
    return HttpResponse(content=json.dumps(data), content_type='application/json')


@api_view(['GET'])
def publication(request: Request, uid: uuid.UUID) -> HttpResponse:
    res = raw_redirect_with_query(request, f'{ServiceUrl.PUBLICATION}/api/v1/publications/{uid}/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    data = {'publication': res.json()}
    replace_author(data['publication'])

    res = raw_redirect_with_query(request, f'{ServiceUrl.PUBLICATION}/api/v1/comments/?publication={uid}')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    data.update(res.json())
    replace_authors(data['items'])

    return HttpResponse(content=json.dumps(data), content_type='application/json')


@api_view(['GET'])
def comments(request: Request) -> HttpResponse:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/comments/')
