import json
import os
import uuid

import requests

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.views import APIView


class ServiceUrl:
    SESSION = os.getenv('BLOG_BACKEND_SESSION_URL', 'http://127.0.0.1:8082')
    PUBLICATION = os.getenv('BLOG_BACKEND_PUBLICATION_URL', 'http://127.0.0.1:8083')
    SUBSCRIPTION = os.getenv('BLOG_BACKEND_SUBSCRIPTION_URL', 'http://127.0.0.1:8084')
    STATISTICS = os.getenv('BLOG_BACKEND_STATISTICS_URL', 'http://127.0.0.1:8085')


def raw_request_get_no_query(url: str) -> requests.Response:
    return requests.get(url)


def raw_redirect_get_with_query(request: Request, url: str) -> requests.Response:
    return requests.get(url, request.query_params)


def make_response(res: requests.Response) -> HttpResponse:
    return HttpResponse(content=res.content, status=res.status_code, content_type=res.headers.get('content-type'))


def redirect(request: Request, url: str) -> HttpResponse:
    return make_response(requests.request(request.method, url, params=request.query_params, data=request.data))


def api_view_redirect(http_method_names: list[str], url: str):
    @api_view(http_method_names)
    def redirect_auto(_request: Request):
        return redirect(_request, url)

    return redirect_auto


# Session Service

users = api_view_redirect(['GET', 'POST'], f'{ServiceUrl.SESSION}/api/v1/users/')
user_by_token = api_view_redirect(['POST'], f'{ServiceUrl.SESSION}/api/v1/user-by-token/')


@api_view(['GET'])
def user(request: Request, uid: uuid.UUID) -> HttpResponse:
    return redirect(request, f'{ServiceUrl.SESSION}/api/v1/users/{uid}/')


# Subscription Service

subscriptions = api_view_redirect(['GET', 'POST'], f'{ServiceUrl.SUBSCRIPTION}/api/v1/subscriptions/')


@api_view(['GET', 'DELETE'])
def subscription(request: Request, uid: uuid.UUID) -> HttpResponse:
    return redirect(request, f'{ServiceUrl.SUBSCRIPTION}/api/v1/subscriptions/{uid}/')


# Publication Service

tags = api_view_redirect(['GET'], f'{ServiceUrl.PUBLICATION}/api/v1/tags/')
votes = api_view_redirect(['GET'], f'{ServiceUrl.PUBLICATION}/api/v1/votes/')
vote = api_view_redirect(['POST'], f'{ServiceUrl.PUBLICATION}/api/v1/vote/')


@api_view(['GET'])
def tag(request: Request, name: str) -> HttpResponse:
    return redirect(request, f'{ServiceUrl.PUBLICATION}/api/v1/tags/{name}/')


@api_view(['GET'])
def tag_uid(request: Request, uid: uuid.UUID) -> HttpResponse:
    return redirect(request, f'{ServiceUrl.PUBLICATION}/api/v1/tags_uid/{uid}/')


def replace_user(item, uid_field, new_field):
    res = raw_request_get_no_query(f'{ServiceUrl.SESSION}/api/v1/users/{item[uid_field]}/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)  # TODO
    item[new_field] = res.json()
    del item[uid_field]


def replace_author(item):
    return replace_user(item, 'author_uid', 'author')


def replace_authors(items):
    for item in items:
        replace_author(item)


def replace_tags(request: Request):
    tags = request.data['tags'].split()
    for tag in tags:
        res = raw_request_get_no_query(f'{ServiceUrl.PUBLICATION}/api/v1/tags/{tag}/')
        if res.status_code == status.HTTP_404_NOT_FOUND:
            res = requests.post(f'{ServiceUrl.PUBLICATION}/api/v1/tags/', json={'name': tag})
            if res.status_code != status.HTTP_201_CREATED:
                return make_response(res)
    request.data['tags'] = tags


class Publications(APIView):
    @staticmethod
    def get(request: Request) -> HttpResponse:
        res = raw_redirect_get_with_query(request, f'{ServiceUrl.PUBLICATION}/api/v1/publications/')
        if res.status_code != status.HTTP_200_OK:
            return make_response(res)
        data = res.json()
        replace_authors(data['items'])
        return HttpResponse(content=json.dumps(data), content_type='application/json')

    @staticmethod
    def post(request: Request) -> HttpResponse:
        replace_tags(request)
        return redirect(request, f'{ServiceUrl.PUBLICATION}/api/v1/publications/')


class Publication(APIView):
    @staticmethod
    def get(request: Request, uid: uuid.UUID) -> HttpResponse:
        res = raw_redirect_get_with_query(request, f'{ServiceUrl.PUBLICATION}/api/v1/publications/{uid}/')
        if res.status_code != status.HTTP_200_OK:
            return make_response(res)
        data = {'publication': res.json()}
        replace_author(data['publication'])

        res = raw_redirect_get_with_query(request, f'{ServiceUrl.PUBLICATION}/api/v1/comments/?publication={uid}')
        if res.status_code != status.HTTP_200_OK:
            return make_response(res)
        data.update(res.json())
        replace_authors(data['items'])

        stat = {'publication_uid': data['publication']['id']}
        if viewer_uid := request.query_params.get('viewer_uid'):
            stat['viewer_uid'] = viewer_uid
        res = requests.post(f'{ServiceUrl.STATISTICS}/api/v1/statistics/', json=stat)
        # no matter

        return HttpResponse(content=json.dumps(data), content_type='application/json')

    @staticmethod
    def patch(request: Request, uid: uuid.UUID) -> HttpResponse:
        if 'tags' in request.data:
            replace_tags(request)
        return redirect(request, f'{ServiceUrl.PUBLICATION}/api/v1/publications/{uid}/')

    @staticmethod
    def delete(request: Request, uid: uuid.UUID) -> HttpResponse:
        return redirect(request, f'{ServiceUrl.PUBLICATION}/api/v1/publications/{uid}/')


comments = api_view_redirect(['GET', 'POST'], f'{ServiceUrl.PUBLICATION}/api/v1/comments/')


@api_view(['GET', 'PATCH', 'DELETE'])
def comment(request: Request, uid: uuid.UUID) -> HttpResponse:
    return redirect(request, f'{ServiceUrl.PUBLICATION}/api/v1/comments/{uid}/')


# Statistics Service


@api_view(['GET'])
def statistics(request: Request, uid: uuid.UUID) -> HttpResponse:
    res = raw_request_get_no_query(f'{ServiceUrl.PUBLICATION}/api/v1/publications/{uid}/')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    data = {'publication': res.json()}

    replace_author(data['publication'])

    res = raw_redirect_get_with_query(request, f'{ServiceUrl.STATISTICS}/api/v1/statistics/?publication_uid={uid}')
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)

    data.update(res.json())

    for item in data['items']:
        if item['viewer_uid']:
            res = replace_user(item, 'viewer_uid', 'viewer')
        else:
            item['viewer'] = '%%guest%%'
            del item['viewer_uid']

    return HttpResponse(content=json.dumps(data), content_type='application/json')
