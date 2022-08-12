import os
import requests
import uuid

from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, View
from rest_framework import status

from .forms import LoginForm, RegisterForm, PublicationForm, CommentForm, EmptyForm


class ServiceUrl:
    GATEWAY = os.getenv('BACKEND_GATEWAY_URL', 'http://localhost:8081')
    SESSION = os.getenv('BACKEND_SESSION_URL', 'http://localhost:8082')


class HttpResponseUnauthorized(HttpResponse):
    status_code = status.HTTP_401_UNAUTHORIZED


class ContextPassUserMixin:
    cached_context = None

    def get_context_data(self, **kwargs):
        if self.cached_context is None:
            self.cached_context = super().get_context_data(**kwargs)
            self.cached_context['user'] = get_auth_user(self.request)
        return self.cached_context


class LoginRequiredMixin(ContextPassUserMixin):
    def render_to_response(self, context, **kwargs):
        if not context['user']['is_authenticated']:
            return HttpResponseUnauthorized()
        return super().render_to_response(context, **kwargs)


class GuestRequiredMixin(ContextPassUserMixin):
    def render_to_response(self, context, **kwargs):
        if context['user']['is_authenticated']:
            return HttpResponseBadRequest('You are already logged in')
        return super().render_to_response(context, **kwargs)


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


def add_error_in_form(form, data):
    if 'detail' in data:
        form.add_error(None, data['detail'])
    else:
        form.add_error(None, data)


class LoginView(GuestRequiredMixin, FormView):
    template_name = 'blog/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('blog:feed')

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form: RegisterForm) -> HttpResponse:
        res = request_auth_tokens(form)
        if res.status_code != status.HTTP_200_OK:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        ret = super().form_valid(form)
        set_auth_tokens(ret, res.json())
        return ret


class RegisterView(GuestRequiredMixin, FormView):
    template_name = 'blog/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('blog:feed')

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form: RegisterForm) -> HttpResponse:
        res = requests.post(ServiceUrl.GATEWAY + '/api/v1/users/',
                            json=create_json_from_form(form,
                                                       ['username', 'password', 'first_name', 'last_name', 'email']))
        if res.status_code != status.HTTP_201_CREATED:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        res = request_auth_tokens(form)
        if res.status_code != status.HTTP_200_OK:
            print(res)
            raise Exception(res.json())
        ret = super().form_valid(form)
        set_auth_tokens(ret, res.json())
        return ret


class PublicationCreateView(LoginRequiredMixin, FormView):
    template_name = 'blog/create.html'
    form_class = PublicationForm

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form: PublicationForm) -> HttpResponse:
        user = get_auth_user(self.request)
        if not user['is_authenticated']:
            form.add_error(None, 'Access token expired, please re-login')
            return super().form_invalid(form)
        res = requests.post(f'{ServiceUrl.GATEWAY}/api/v1/publications/',
                            json=create_json_from_form(form, ['title', 'tags', 'body']) | {'author_uid': user['id']})
        if res.status_code != status.HTTP_201_CREATED:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:user_publications', args=[self.get_context_data()["user"]["username"]])


class PublicationDeleteView(LoginRequiredMixin, FormView):
    template_name = 'blog/confirm-delete.html'
    form_class = EmptyForm

    def get_context_data(self, **kwargs):
        if self.cached_context is None:
            self.cached_context = super().get_context_data(**kwargs)
            res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/publications/{self.cached_context["view"].kwargs["pk"]}/')
            self.cached_context['object'] = res.json()
            if 'publication' in self.cached_context['object']:
                self.cached_context['object'] = self.cached_context['object']['publication']
            self.cached_context['request_status'] = res.status_code
        return self.cached_context

    def render_to_response(self, context, **kwargs):
        if not context['user']['is_authenticated']:
            return HttpResponseUnauthorized('Unauthorized')
        if context['request_status'] != status.HTTP_200_OK:
            return HttpResponseBadRequest(context['object'])
        if context['object']['author']['id'] != context['user']['id']:
            return HttpResponseUnauthorized('Can\'t delete publication of other user')
        return super().render_to_response(context, **kwargs)

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form) -> HttpResponse:
        user = get_auth_user(self.request)
        if not user['is_authenticated']:
            form.add_error(None, 'Access token expired, please re-login')
            return super().form_invalid(form)
        res = requests.delete(f'{ServiceUrl.GATEWAY}/api/v1/publications/{self.get_context_data()["view"].kwargs["pk"]}/')
        if res.status_code != status.HTTP_204_NO_CONTENT:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:feed')


class CommentCreateView(LoginRequiredMixin, FormView):
    template_name = 'blog/create.html'
    form_class = CommentForm

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form: CommentForm) -> HttpResponse:
        user = get_auth_user(self.request)
        if not user['is_authenticated']:
            form.add_error(None, 'Access token expired, please re-login')
            return super().form_invalid(form)
        res = requests.post(f'{ServiceUrl.GATEWAY}/api/v1/comments/',
                            json=create_json_from_form(form, ['body'])
                                 | {'author_uid': user['id'],
                                    'publication': str(self.get_context_data()['view'].kwargs['pk'])})
        if res.status_code != status.HTTP_201_CREATED:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:publications', args=[str(self.get_context_data()["view"].kwargs["pk"])])


class CommentManipulateMixin:
    def get_context_data(self, **kwargs):
        if self.cached_context is None:
            self.cached_context = super().get_context_data(**kwargs)
            res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/comments/{self.cached_context["view"].kwargs["pk"]}/')
            self.cached_context['request_status'] = res.status_code
            self.cached_context['object'] = res.json()
        return self.cached_context

    def render_to_response(self, context, **kwargs):
        if context['request_status'] != status.HTTP_200_OK:
            return HttpResponseBadRequest(context['object'])
        if context['object']['author_uid'] != context['user']['id']:
            return HttpResponseUnauthorized('Can\'t manipulate comment of other user')
        return super().render_to_response(context, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:publications', args=[self.get_context_data()["object"]["publication"]])


class CommentUpdateView(CommentManipulateMixin, LoginRequiredMixin, FormView):
    template_name = 'blog/create.html'
    form_class = CommentForm

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form: CommentForm) -> HttpResponse:
        user = get_auth_user(self.request)
        if not user['is_authenticated']:
            form.add_error(None, 'Access token expired, please re-login')
            return super().form_invalid(form)
        res = requests.patch(f'{ServiceUrl.GATEWAY}/api/v1/comments/{self.get_context_data()["view"].kwargs["pk"]}/',
                             json=create_json_from_form(form, ['body']))
        if res.status_code != status.HTTP_200_OK:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        return super().form_valid(form)


class CommentDeleteView(CommentManipulateMixin, LoginRequiredMixin, FormView):
    template_name = 'blog/confirm-delete.html'
    form_class = EmptyForm

    # This method is called when valid form data has been POSTed.
    def form_valid(self, form) -> HttpResponse:
        user = get_auth_user(self.request)
        if not user['is_authenticated']:
            form.add_error(None, 'Access token expired, please re-login')
            return super().form_invalid(form)
        res = requests.delete(f'{ServiceUrl.GATEWAY}/api/v1/comments/{self.get_context_data()["view"].kwargs["pk"]}/')
        if res.status_code != status.HTTP_204_NO_CONTENT:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        return super().form_valid(form)


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


class VoteView(View):
    content_type = None
    value = None

    def post(self, request, pk: uuid.UUID):
        user = get_auth_user(request)
        res = requests.post(f'{ServiceUrl.GATEWAY}/api/v1/vote/', json={
            'value': self.value,
            'user_uid': user['id'],
            'content_type': self.content_type,
            'object_id': str(pk),
        })
        if res.status_code != status.HTTP_200_OK:
            print(res)
            raise Exception(res.json())

        return HttpResponse(content=res.content, content_type="application/json")


def publication_update_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def publication_delete_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request)})


def tag_view(request: HttpRequest, tag: str) -> HttpResponse:
    res = paginated_request_get(request, f'{ServiceUrl.GATEWAY}/api/v1/publications/?tags__name={tag}')
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(res.json())
    return render(request, 'blog/publication-list.html', {
        'user': get_auth_user(request),
        'tag': tag,
        'response': res.json(),
    })
