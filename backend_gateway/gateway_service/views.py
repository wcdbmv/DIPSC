import json
import os
import queue
import requests
import threading
import time
import uuid

from circuitbreaker import circuit, CircuitBreakerError
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.views import APIView


QUEUE = queue.Queue()


def worker():
    while True:
        callback = QUEUE.get()
        stop_event = threading.Event()

        def call():
            while not stop_event.is_set():
                try:
                    callback()
                    break
                except Exception as e:
                    print(e)
                    print('RETRY IN 5')
                    time.sleep(5)

        thread = threading.Thread(target=call)
        thread.start()
        thread.join(timeout=10)
        if thread.is_alive():
            stop_event.set()
            thread.join()
            QUEUE.put(callback)
        QUEUE.task_done()


# turn-on the worker thread
threading.Thread(target=worker).start()


class ServiceUrl:
    SESSION = os.getenv('BLOG_BACKEND_SESSION_URL', 'http://127.0.0.1:8082')
    PUBLICATION = os.getenv('BLOG_BACKEND_PUBLICATION_URL', 'http://127.0.0.1:8083')
    SUBSCRIPTION = os.getenv('BLOG_BACKEND_SUBSCRIPTION_URL', 'http://127.0.0.1:8084')
    STATISTICS = os.getenv('BLOG_BACKEND_STATISTICS_URL', 'http://127.0.0.1:8085')


def req(method: str, url: str, **kwargs) -> requests.Response:
    res = requests.request(method, url, **kwargs)
    if res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        res.raise_for_status()
    return res


@circuit
def session_request(method: str, path: str, **kwargs) -> requests.Response:
    return req(method, f'{ServiceUrl.SESSION}{path}', **kwargs)


@circuit
def publication_request(method: str, path: str, **kwargs) -> requests.Response:
    return req(method, f'{ServiceUrl.PUBLICATION}{path}', **kwargs)


@circuit
def subscription_request(method: str, path: str, **kwargs) -> requests.Response:
    return req(method, f'{ServiceUrl.SUBSCRIPTION}{path}', **kwargs)


@circuit
def statistics_request(method: str, path: str, **kwargs) -> requests.Response:
    return req(method, f'{ServiceUrl.STATISTICS}{path}', **kwargs)


def circuit_redirect(request: Request, func_request, path: str):
    return func_request(request.method, path, params=request.query_params, data=request.data)


def make_response(res: requests.Response) -> HttpResponse:
    return HttpResponse(content=res.content, status=res.status_code, content_type=res.headers.get('content-type'))


def unavailable(service_name, error: requests.HTTPError | CircuitBreakerError):
    if isinstance(error, CircuitBreakerError):
        return HttpResponse(
            content=f'{service_name} service is unavailable [circuit break]: {error}'.encode(),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    else:
        return HttpResponse(
            content=f'{service_name} service is unavailable'.encode(),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def raw_try_except_circuit_redirect(request: Request, service_name: str, circuit_request, path):
    try:
        return make_response(circuit_redirect(request, circuit_request, path))
    except (requests.HTTPError, CircuitBreakerError) as e:
        return unavailable(service_name, e)


def circuit_api_view_redirect(http_method_names: list[str], service_name, circuit_request, path):
    @api_view(http_method_names)
    def try_except_circuit_redirect(request: Request):
        return raw_try_except_circuit_redirect(request, service_name, circuit_request, path)

    return try_except_circuit_redirect


# Session Service

users = circuit_api_view_redirect(['GET', 'POST'], 'Session', session_request, '/api/v1/users')
user_by_token = circuit_api_view_redirect(['POST'], 'Session', session_request, '/api/v1/user-by-token/')


@api_view(['GET'])
def user(request: Request, uid: uuid.UUID) -> HttpResponse:
    return raw_try_except_circuit_redirect(request, 'Session', session_request, f'/api/v1/users/{uid}/')


# Subscription Service

subscriptions = circuit_api_view_redirect(['GET', 'POST'], 'Subscription', subscription_request,
                                          '/api/v1/subscriptions/')


@api_view(['GET', 'DELETE'])
def subscription(request: Request, uid: uuid.UUID) -> HttpResponse:
    return raw_try_except_circuit_redirect(request, 'Subscription', subscription_request,
                                           f'/api/v1/subscriptions/{uid}/')


# Publication Service

tags = circuit_api_view_redirect(['GET'], 'Publication', publication_request, '/api/v1/tags/')
votes = circuit_api_view_redirect(['GET'], 'Publication', publication_request, '/api/v1/votes/')
vote = circuit_api_view_redirect(['POST'], 'Publication', publication_request, '/api/v1/vote/')


@api_view(['GET'])
def tag(request: Request, name: str) -> HttpResponse:
    return raw_try_except_circuit_redirect(request, 'Publication', publication_request, f'/api/v1/tags/{name}/')


@api_view(['GET'])
def tag_uid(request: Request, uid: uuid.UUID) -> HttpResponse:
    return raw_try_except_circuit_redirect(request, 'Publication', publication_request, f'/api/v1/tags_uid/{uid}/')


def replace_user(item, uid_field, new_field) -> HttpResponse | None:
    try:
        res = session_request('GET', f'/api/v1/users/{item[uid_field]}/')
    except (requests.HTTPError, CircuitBreakerError) as e:
        return unavailable('Session', e)
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    item[new_field] = res.json()
    del item[uid_field]


def replace_author(item) -> HttpResponse | None:
    return replace_user(item, 'author_uid', 'author')


def replace_authors(items) -> HttpResponse | None:
    for item in items:
        res = replace_author(item)
        if res is not None:
            return res


def replace_tags(request: Request) -> HttpResponse | None:
    _tags = request.data['tags'].split()
    for _tag in _tags:
        try:
            res = publication_request('GET', f'/api/v1/tags/{_tag}/')
        except (requests.HTTPError, CircuitBreakerError) as e:
            return unavailable('Publication', e)

        if res.status_code == status.HTTP_404_NOT_FOUND:
            try:
                res = publication_request('POST', '/api/v1/tags/', json={'name': _tag})
            except (requests.HTTPError, CircuitBreakerError) as e:
                return unavailable('Publication', e)

            if res.status_code != status.HTTP_201_CREATED:
                return make_response(res)
    request.data['tags'] = _tags


class Publications(APIView):
    @staticmethod
    def get(request: Request) -> HttpResponse:
        try:
            res = publication_request('GET', '/api/v1/publications/', params=request.query_params)
        except (requests.HTTPError, CircuitBreakerError) as e:
            return unavailable('Publication', e)

        if res.status_code != status.HTTP_200_OK:
            return make_response(res)
        data = res.json()
        err = replace_authors(data['items'])
        if err is not None:
            return err

        return HttpResponse(content=json.dumps(data), content_type='application/json')

    @staticmethod
    def post(request: Request) -> HttpResponse:
        err = replace_tags(request)
        if err is not None:
            return err
        return raw_try_except_circuit_redirect(request, 'Publication', publication_request, '/api/v1/publications/')


class Publication(APIView):
    @staticmethod
    def get(request: Request, uid: uuid.UUID) -> HttpResponse:
        try:
            res = publication_request('GET', f'/api/v1/publications/{uid}/', params=request.query_params)
        except (requests.HTTPError, CircuitBreakerError) as e:
            return unavailable('Publication', e)
        if res.status_code != status.HTTP_200_OK:
            return make_response(res)

        data = {'publication': res.json()}
        err = replace_author(data['publication'])
        if err is not None:
            return err

        try:
            res = publication_request('GET', f'/api/v1/comments/?publication={uid}', params=request.query_params)
        except (requests.HTTPError, CircuitBreakerError) as e:
            return unavailable('Publication', e)
        if res.status_code != status.HTTP_200_OK:
            return make_response(res)

        data.update(res.json())
        err = replace_authors(data.get('items', []))
        if err is not None:
            return err

        stat = {'publication_uid': data['publication']['id']}
        if viewer_uid := request.query_params.get('viewer_uid'):
            stat['viewer_uid'] = viewer_uid

        def post_stat():
            statistics_request('POST', '/api/v1/statistics/', json=stat)
        QUEUE.put(post_stat)

        return HttpResponse(content=json.dumps(data), content_type='application/json')

    @staticmethod
    def patch(request: Request, uid: uuid.UUID) -> HttpResponse:
        if 'tags' in request.data:
            err = replace_tags(request)
            if err is not None:
                return err
        return raw_try_except_circuit_redirect(request, 'Publication', publication_request,
                                               f'/api/v1/publications/{uid}/')

    @staticmethod
    def delete(request: Request, uid: uuid.UUID) -> HttpResponse:
        return raw_try_except_circuit_redirect(request, 'Publication', publication_request,
                                               f'/api/v1/publications/{uid}/')


comments = circuit_api_view_redirect(['GET', 'POST'], 'Publication', publication_request, '/api/v1/comments/')


@api_view(['GET', 'PATCH', 'DELETE'])
def comment(request: Request, uid: uuid.UUID) -> HttpResponse:
    return raw_try_except_circuit_redirect(request, 'Publication', publication_request, f'/api/v1/comments/{uid}/')


# Statistics Service

@api_view(['GET'])
def statistics(request: Request, uid: uuid.UUID) -> HttpResponse:
    try:
        res = publication_request('GET', f'/api/v1/publications/{uid}/')
    except (requests.HTTPError, CircuitBreakerError) as e:
        return unavailable('Publication', e)
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)
    data = {'publication': res.json()}

    err = replace_author(data['publication'])
    if err is not None:
        return err

    try:
        res = statistics_request('GET', f'/api/v1/statistics/?publication_uid={uid}', params=request.query_params)
    except (requests.HTTPError, CircuitBreakerError) as e:
        return unavailable('Statistics', e)
    if res.status_code != status.HTTP_200_OK:
        return make_response(res)

    data.update(res.json())

    for item in data['items']:
        if item['viewer_uid']:
            err = replace_user(item, 'viewer_uid', 'viewer')
            if err is not None:
                return err
        else:
            item['viewer'] = '%%guest%%'
            del item['viewer_uid']

    return HttpResponse(content=json.dumps(data), content_type='application/json')
