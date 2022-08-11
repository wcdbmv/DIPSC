import os
import requests
import uuid

from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views.generic.edit import FormView
from rest_framework import status

from .forms import LoginForm, RegisterForm


class ServiceUrl:
    GATEWAY = os.getenv('BACKEND_GATEWAY_URL', 'http://localhost:8081')
    SESSION = os.getenv('BACKEND_SESSION_URL', 'http://localhost:8082')


def create_json_from_form(form, fields) -> dict:
    return {field: form.data[field] for field in fields}


def request_auth_tokens(form) -> requests.Response:
    return requests.post(ServiceUrl.SESSION + '/api/token/', json=create_json_from_form(form, ['username', 'password']))


def set_auth_tokens(response: HttpResponse, tokens):
    response.set_cookie('access_token', tokens['access'], httponly=True)
    response.set_cookie('refresh_token', tokens['refresh'], httponly=True)


def get_auth_user(request: HttpRequest) -> dict:
    access_token = request.COOKIES.get('access_token')
    if access_token is None:
        return {'is_authenticated': False}
    res = requests.post(ServiceUrl.GATEWAY + '/api/v1/user-by-token/', json={'token': access_token})
    if res.status_code != status.HTTP_200_OK:
        return {'is_authenticated': False}
    return {'is_authenticated': True, **res.json()}


class LoginView(FormView):
    template_name = 'blog/login.html'
    form_class = LoginForm
    success_url = '/blog/feed/'

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form: RegisterForm) -> HttpResponse:
        res = request_auth_tokens(form)
        if res.status_code != status.HTTP_200_OK:
            form.add_error(None, res.json())
            return super().form_invalid(form)
        ret = super().form_valid(form)
        set_auth_tokens(ret, res.json())
        return ret


class RegisterView(FormView):
    template_name = 'blog/register.html'
    form_class = RegisterForm
    success_url = '/blog/feed/'

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form: RegisterForm) -> HttpResponse:
        res = requests.post(ServiceUrl.GATEWAY + '/api/v1/users/',
                            json=create_json_from_form(form,
                                                       ['username', 'password', 'first_name', 'last_name', 'email']))
        if res.status_code != status.HTTP_201_CREATED:
            form.add_error(None, res.json())
            return super().form_invalid(form)
        res = request_auth_tokens(form)
        if res.status_code != status.HTTP_200_OK:
            print(res)
            raise Exception(res.json())
        ret = super().form_valid(form)
        set_auth_tokens(ret, res.json())
        return ret


def paginated_request_get(request: HttpRequest, url) -> requests.Response:
    params = request.GET.copy()
    params['page'] = params.get('page', 1)
    params['page_size'] = params.get('page_size', 10)
    return requests.get(url, params)


def feed_view(request: HttpRequest) -> HttpResponse:
    res = paginated_request_get(request, ServiceUrl.GATEWAY + '/api/v1/publications/')
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request), 'response': res.json()})


def blog_view(request: HttpRequest, username: str) -> HttpResponse:
    res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/users/?username={username}')
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(res.json())
    data = res.json()
    if len(data) == 0:
        return HttpResponseNotFound(f'User with username "{username}" not found')
    user = data[0]
    res = paginated_request_get(request, f'{ServiceUrl.GATEWAY}/api/v1/publications/?author_uid={user["id"]}')
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise res
    return render(request, 'blog/publication-list.html', {
        'user': get_auth_user(request),
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'response': res.json(),
    })


def publication_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    res = paginated_request_get(request, f'{ServiceUrl.GATEWAY}/api/v1/publications/{pk}/')
    if res.status_code != status.HTTP_200_OK:
        if res.status_code == status.HTTP_404_NOT_FOUND:
            return HttpResponseNotFound(f'Publication with uuid {pk} not found')
        print(res)
        raise res
    return render(request, 'blog/publication.html', {'user': get_auth_user(request), 'response': res.json()})


def publication_upvote_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_downvote_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_create_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_update_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_delete_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_create_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_update_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_delete_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def tag_view(request: HttpRequest, tag: str) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_upvote_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_downvote_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})
