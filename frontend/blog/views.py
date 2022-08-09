import requests
import uuid

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView
from rest_framework import status
from rest_framework.request import Request

from .forms import LoginForm, RegisterForm


class ServiceUrl:
    GATEWAY = 'http://localhost:8081'
    SESSION = 'http://localhost:8082'


def create_json_from_form(form, fields) -> dict:
    return {field: form.data[field] for field in fields}


def request_auth_tokens(form) -> requests.Response:
    return requests.post(ServiceUrl.SESSION + '/api/token/', json=create_json_from_form(form, ['username', 'password']))


def set_auth_tokens(response: HttpResponse, tokens):
    response.set_cookie('access_token', tokens['access'], httponly=True)
    response.set_cookie('refresh_token', tokens['refresh'], httponly=True)


def get_auth_user(request: Request) -> dict:
    access_token = request.COOKIES['access_token']
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
            raise res
        ret = super().form_valid(form)
        set_auth_tokens(ret, res.json())
        return ret


def feed_view(request: Request) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def blog_view(request: Request, username: str) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_upvote_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_downvote_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_create_view(request: Request) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_update_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_delete_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_create_view(request: Request) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_update_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_delete_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def tag_view(request: Request, tag: str) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_upvote_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def comment_downvote_view(request: Request, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})
