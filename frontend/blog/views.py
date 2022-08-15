import os
import requests
import uuid

from django import forms
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, View
from rest_framework import status

from .forms import LoginForm, RegisterForm, PublicationForm, CommentForm, EmptyForm


class ServiceUrl:
    GATEWAY = os.getenv('BLOG_BACKEND_GATEWAY_URL', 'http://localhost:8081')
    SESSION = os.getenv('BLOG_BACKEND_SESSION_URL', 'http://localhost:8082')


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
    is_authenticated = True
    auth_error_response = HttpResponseUnauthorized()

    def render_to_response(self, context, **kwargs):
        if context['user']['is_authenticated'] != self.is_authenticated:
            return self.auth_error_response
        return super().render_to_response(context, **kwargs)


class GuestRequiredMixin(LoginRequiredMixin):
    is_authenticated = False
    auth_error_response = HttpResponseBadRequest('You are already logged in')


def add_error_in_form(form, data):
    form.add_error(None, data.get('detail', data))


class LoginFormTemplateView(GuestRequiredMixin, FormView):
    success_url = reverse_lazy('blog:publications')

    def form_valid(self, form: LoginForm) -> HttpResponse:
        res = request_auth_tokens(form)
        if res.status_code != status.HTTP_200_OK:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        ret = super().form_valid(form)
        set_auth_tokens(ret, res.json())
        return ret


class LoginView(LoginFormTemplateView):
    template_name = 'blog/login.html'
    form_class = LoginForm


class CheckStatusMixin:
    def check_status(self, res: requests.Response, _status: int, form: forms.Form):
        if res.status_code != _status:
            add_error_in_form(form, res.json())
            return super().form_invalid(form)
        return super().form_valid(form)


class RegisterView(CheckStatusMixin, LoginFormTemplateView):
    template_name = 'blog/register.html'
    form_class = RegisterForm

    def form_valid(self, form: RegisterForm) -> HttpResponse:
        data = create_json_from_form(form, ['username', 'password', 'first_name', 'last_name', 'email'])
        res = requests.post(ServiceUrl.GATEWAY + '/api/v1/users/', json=data)
        return self.check_status(res, status.HTTP_201_CREATED, form)  # call LoginFormTemplateView.form_valid


def logout_view(request: HttpRequest) -> HttpResponse:
    ret = redirect('blog:publications')
    set_auth_tokens(ret, {'access': None, 'refresh': None})
    return ret


def get_auth_user_or_add_form_error(request: HttpRequest, form: forms.Form):
    user = get_auth_user(request)
    if not user['is_authenticated']:
        form.add_error(None, 'Access token expired, please re-login')
        return None
    return user


class PublicationCreateView(CheckStatusMixin, LoginRequiredMixin, FormView):
    template_name = 'blog/create.html'
    form_class = PublicationForm

    def form_valid(self, form: PublicationForm) -> HttpResponse:
        if not (user := get_auth_user_or_add_form_error(self.request, form)):
            return super().form_invalid(form)

        data = create_json_from_form(form, ['title', 'tags', 'body']) | {'author_uid': user['id']}
        res = requests.post(f'{ServiceUrl.GATEWAY}/api/v1/publications/', json=data)
        return self.check_status(res, status.HTTP_201_CREATED, form)

    def get_success_url(self):
        return reverse_lazy('blog:user_publications', args=[self.get_context_data()["user"]["username"]])


class ManipulateMixinBase(CheckStatusMixin, LoginRequiredMixin):
    obj = None

    def insert_object_in_context(self, data):
        self.cached_context['object'] = data

    def get_context_data(self, **kwargs):
        if self.cached_context is None:
            self.cached_context = super().get_context_data(**kwargs)
            res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/{self.obj}s/{self.cached_context["view"].kwargs["pk"]}/')
            self.cached_context['request_status'] = res.status_code
            self.insert_object_in_context(res.json())
        return self.cached_context

    def get_author_uid(self, context):
        return context['object']['author_uid']

    def render_to_response(self, context, **kwargs):
        if not context['user']['is_authenticated']:
            return HttpResponseUnauthorized('Access token expired, please re-login')
        if context['request_status'] != status.HTTP_200_OK:
            return HttpResponseBadRequest(context['object'])
        if self.get_author_uid(context) != context['user']['id']:
            return HttpResponseUnauthorized(f'Can\'t manipulate {self.obj} of other user')
        return super().render_to_response(context, **kwargs)


class PublicationManipulateMixin(ManipulateMixinBase):
    obj = 'publication'

    def insert_object_in_context(self, data):
        self.cached_context['object'] = data
        if 'publication' in self.cached_context['object']:
            self.cached_context['object'] = self.cached_context['object']['publication']

    def get_author_uid(self, context):
        return context['object']['author']['id']


class PublicationUpdateView(PublicationManipulateMixin, FormView):
    template_name = 'blog/create.html'
    form_class = PublicationForm

    def form_valid(self, form: PublicationForm) -> HttpResponse:
        if not get_auth_user_or_add_form_error(self.request, form):
            return super().form_invalid(form)

        url = f'{ServiceUrl.GATEWAY}/api/v1/publications/{self.get_context_data()["view"].kwargs["pk"]}/'
        res = requests.patch(url, json=create_json_from_form(form, ['title', 'tags', 'body']))
        return self.check_status(res, status.HTTP_200_OK, form)

    def get_success_url(self):
        return reverse_lazy('blog:publication', args=[self.cached_context["view"].kwargs["pk"]])


class PublicationDeleteView(PublicationManipulateMixin, FormView):
    template_name = 'blog/confirm-delete.html'
    form_class = EmptyForm
    success_url = reverse_lazy('blog:publications')

    def form_valid(self, form) -> HttpResponse:
        if not get_auth_user_or_add_form_error(self.request, form):
            return super().form_invalid(form)

        url = f'{ServiceUrl.GATEWAY}/api/v1/publications/{self.get_context_data()["view"].kwargs["pk"]}/'
        res = requests.delete(url)
        return self.check_status(res, status.HTTP_204_NO_CONTENT, form)


class CommentCreateView(CheckStatusMixin, LoginRequiredMixin, FormView):
    template_name = 'blog/create.html'
    form_class = CommentForm

    def form_valid(self, form: CommentForm) -> HttpResponse:
        if not (user := get_auth_user_or_add_form_error(self.request, form)):
            return super().form_invalid(form)

        data = create_json_from_form(form, ['body']) | {
            'author_uid': user['id'],
            'publication': str(self.get_context_data()['view'].kwargs['pk'])
        }
        res = requests.post(f'{ServiceUrl.GATEWAY}/api/v1/comments/', json=data)
        return self.check_status(res, status.HTTP_201_CREATED, form)

    def get_success_url(self):
        return reverse_lazy('blog:publication', args=[str(self.get_context_data()["view"].kwargs["pk"])])


class CommentManipulateMixin(ManipulateMixinBase):
    obj = 'comment'

    def get_success_url(self):
        return reverse_lazy('blog:publication', args=[self.get_context_data()['object']['publication']])


class CommentUpdateView(CommentManipulateMixin, FormView):
    template_name = 'blog/create.html'
    form_class = CommentForm

    def form_valid(self, form: CommentForm) -> HttpResponse:
        if not get_auth_user_or_add_form_error(self.request, form):
            return super().form_invalid(form)

        url = f'{ServiceUrl.GATEWAY}/api/v1/comments/{self.get_context_data()["view"].kwargs["pk"]}/'
        res = requests.patch(url, json=create_json_from_form(form, ['body']))
        return self.check_status(res, status.HTTP_200_OK, form)


class CommentDeleteView(CommentManipulateMixin, FormView):
    template_name = 'blog/confirm-delete.html'
    form_class = EmptyForm

    def form_valid(self, form) -> HttpResponse:
        if not get_auth_user_or_add_form_error(self.request, form):
            return super().form_invalid(form)

        res = requests.delete(f'{ServiceUrl.GATEWAY}/api/v1/comments/{self.get_context_data()["view"].kwargs["pk"]}/')
        return self.check_status(res, status.HTTP_204_NO_CONTENT, form)


def set_page_params(params):
    params['page'] = params.get('page', 1)
    params['page_size'] = params.get('page_size', 10)


def paginated_request_get(request: HttpRequest, url) -> requests.Response:
    params = request.GET.copy()
    set_page_params(params)
    return requests.get(url, params)


def publications_view(request: HttpRequest) -> HttpResponse:
    res = paginated_request_get(request, ServiceUrl.GATEWAY + '/api/v1/publications/')
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request), 'response': res.json()})


def check_subscribed(follower_uid, following_uid, return_subscription_uid=False):
    res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/', {
        'follower_uid': follower_uid,
        'following_uid': following_uid,
    })

    subscribed = None
    if res.status_code == status.HTTP_200_OK:
        data = res.json()
        subscribed = len(data) > 0
        if subscribed and return_subscription_uid:
            subscribed = data[0]['subscription_uid']

    return subscribed


def get_user_by_username(username: str):
    res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/users/?username={username}')
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(res.json())
    data = res.json()
    if len(data) == 0:
        return None
    return data[0]


def get_tag_by_name(name: str):
    res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/tags/{name}/')
    if res.status_code != status.HTTP_200_OK:
        if res.status_code == status.HTTP_404_NOT_FOUND:
            return {}
        print(res)
        raise Exception(res.json())
    return res.json()


def blog_view(request: HttpRequest, username: str) -> HttpResponse:
    user = get_user_by_username(username)
    if user is None:
        return HttpResponseNotFound(f'User with username "{username}" not found')

    auth_user = get_auth_user(request)

    subscribed = None
    if auth_user['is_authenticated'] and auth_user['username'] != username:
        subscribed = check_subscribed(auth_user['id'], user['id'])

    res = paginated_request_get(request, f'{ServiceUrl.GATEWAY}/api/v1/publications/?author_uid={user["id"]}')
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(res.json())
    return render(request, 'blog/publication-list.html', {
        'user': auth_user,
        'author_uid': user['id'],
        'username': user['username'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'response': res.json(),
        'subscribed': subscribed,
    })


def publication_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    res = paginated_request_get(request, f'{ServiceUrl.GATEWAY}/api/v1/publications/{pk}/')
    if res.status_code != status.HTTP_200_OK:
        if res.status_code == status.HTTP_404_NOT_FOUND:
            return HttpResponseNotFound(f'Publication with uuid {pk} not found')
        print(res)
        raise Exception(res.json())
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


def tag_view(request: HttpRequest, tag: str) -> HttpResponse:
    auth_user = get_auth_user(request)

    subscribed = None
    if auth_user['is_authenticated']:
        res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/tags/{tag}/')
        if res.status_code != status.HTTP_200_OK:
            if res.status_code == status.HTTP_404_NOT_FOUND:
                return HttpResponseNotFound(f'Tag {tag} not found')
            print(res)
            raise Exception(res.json())
        tag_uid = res.json()['id']
        subscribed = check_subscribed(auth_user['id'], tag_uid)

    res = paginated_request_get(request, f'{ServiceUrl.GATEWAY}/api/v1/publications/?tags__name={tag}')
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(res.json())
    return render(request, 'blog/publication-list.html', {
        'user': auth_user,
        'tag': tag,
        'response': res.json(),
        'subscribed': subscribed,
    })


def feed_view(request: HttpRequest) -> HttpResponse:
    user = get_auth_user(request)
    if not user['is_authenticated']:
        return HttpResponseUnauthorized()

    res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/?follower_uid={user["id"]}')
    if res.status_code != status.HTTP_200_OK:
        return render(request, 'blog/publication-list.html', {'user': user,
                                                              'error_message': 'Subscription service is unavailable'})

    authors = []
    tags = []
    for sub in res.json():
        if sub['type'] == 'user':
            authors.append(sub['following_uid'])
        elif sub['type'] == 'tag':
            tags.append(sub['following_uid'])

    params = request.GET.copy()
    set_page_params(params)
    params['author_uid__in'] = ','.join(authors)
    params['tags__id__in'] = ','.join(tags)
    res = requests.get(f'{ServiceUrl.GATEWAY}/api/v1/publications/', params)
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(res.json())
    return render(request, 'blog/publication-list.html', {'user': user, 'response': res.json()})


class Subscribe(View):
    obj = None
    subscribe = None

    def get(self, request, obj_name: str):
        follower = get_auth_user(request)
        if not follower['is_authenticated']:
            return HttpResponseUnauthorized()

        if self.obj == 'user':
            following = get_user_by_username(obj_name)
        elif self.obj == 'tag':
            following = get_tag_by_name(obj_name)

        subscribed = check_subscribed(follower['id'], following['id'], True)
        if bool(subscribed) == self.subscribe:
            return HttpResponseBadRequest(f'Already {"un" * (not self.subscribe)}subscribed')

        if self.subscribe:
            res = requests.post(f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/', json={
                'follower_uid': follower['id'],
                'following_uid': following['id'],
                'type': self.obj
            })
            if res.status_code != status.HTTP_201_CREATED:
                return HttpResponseBadRequest(res.json())
        else:
            res = requests.delete(f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/{subscribed}/')
            if res.status_code != status.HTTP_204_NO_CONTENT:
                return HttpResponseBadRequest(res.json())

        return redirect('blog:user_publications' if self.obj == 'user' else 'blog:tag', obj_name)


# TODO: create Subscription page
