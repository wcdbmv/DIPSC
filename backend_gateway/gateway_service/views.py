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


def raw_redirect_get(request: Request, url: str) -> requests.Response:
    params = request.query_params.copy()
    params['page'] = params.get('page', 1)
    params['page_size'] = params.get('page_size', 999999)
    return requests.get(url, params)


def make_response(res: requests.Response) -> HttpResponse:
    return HttpResponse(content=res.content, status=res.status_code, content_type=res.headers['content-type'])


def redirect_get(request: Request, url: str) -> HttpResponse:
    return make_response(raw_redirect_get(request, url))


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


@api_view(['GET'])
def publications(request: Request) -> HttpResponse:
    res = raw_redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/publications/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    data = res.json()
    for pub in data['items']:
        res = raw_redirect_get(request, f'{ServiceUrl.SESSION}/api/v1/users/{pub["author_uid"]}/')
        if res.status_code != status.HTTP_200_OK:
            return make_response(res)
        pub['author'] = res.json()
        del pub['author_uid']
    return HttpResponse(content=json.dumps(data), content_type='application/json')


@api_view(['GET'])
def publication(request: Request, uid: uuid.UUID) -> HttpResponse:
    res = raw_redirect_get(request, f'{ServiceUrl.PUBLICATION}/api/v1/publications/{uid}/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    pub = res.json()
    res = raw_redirect_get(request, f'{ServiceUrl.SESSION}/api/v1/users/{pub["author_uid"]}/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    pub['author'] = res.json()
    del pub['author_uid']
    res = raw_redirect_get(request, f'{ServiceUrl.PUBLICATION}/api/v1/comments/?publication={uid}')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    data = res.json()
    data['publication'] = pub
    for comm in data['items']:
        res = raw_redirect_get(request, f'{ServiceUrl.SESSION}/api/v1/users/{comm["author_uid"]}/')
        if res.status_code != status.HTTP_200_OK:
            return make_response(res)
        comm['author'] = res.json()
        del comm['author_uid']
    return HttpResponse(content=json.dumps(data), content_type='application/json')


@api_view(['GET'])
def comments(request: Request) -> HttpResponse:
    return redirect_get(request, ServiceUrl.PUBLICATION + '/api/v1/comments/')
