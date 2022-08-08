import requests

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView
from rest_framework import status
from rest_framework.request import Request

from .forms import RegisterForm


class ServiceUrl:
    GATEWAY = 'http://localhost:8081'
    SESSION = 'http://localhost:8082'


def create_json(form, fields) -> dict:
    return {field: form.data[field] for field in fields}


def get_user(request: Request) -> dict:
    access_token = request.COOKIES['access_token']
    res = requests.post(ServiceUrl.GATEWAY + '/api/v1/user-by-token/', json={'token': access_token})
    if res.status_code != status.HTTP_200_OK:
        return {'is_authenticated': False}
    return {'is_authenticated': True, **res.json()}


class RegisterView(FormView):
    template_name = 'blog/register.html'
    form_class = RegisterForm
    success_url = '/blog/feed/'

    def form_valid(self, form: RegisterForm) -> HttpResponse:
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        res = requests.post(ServiceUrl.GATEWAY + '/api/v1/users/', json=create_json(form, ['username', 'password', 'first_name', 'last_name', 'email']))
        if res.status_code != status.HTTP_201_CREATED:
            js = res.json()
            form.add_error(None, js)
            return super().form_invalid(form)
        res = requests.post(ServiceUrl.SESSION + '/api/token/', json=create_json(form, ['username', 'password']))
        if res.status_code != status.HTTP_200_OK:
            print(res)
            raise res
        data = res.json()
        ret = super().form_valid(form)
        ret.set_cookie('access_token', data['access'], httponly=True)
        ret.set_cookie('refresh_token', data['refresh'], httponly=True)
        return ret


def feed(request: Request):
    return render(request, 'blog/publication-list.html', {'user': get_user(request)})
