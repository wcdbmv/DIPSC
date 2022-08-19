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


def log_request(prompt: str, res: requests.Response) -> (requests.Response, str | dict | list):
    try:
        _json = res.json()
    except requests.JSONDecodeError:
        _json = {}

    print(f'DEBUG-{prompt}-STATUS-CODE', res.status_code)
    print(f'DEBUG-{prompt}-JSON', _json)
    return res, _json


def log_request_get(prompt: str, url: str, params: dict | None = None) -> (requests.Response, str | dict | list):
    res = requests.get(url, params)
    print(f'DEBUG-{prompt}-REQUEST-PARAMS', params)
    return log_request(prompt, res)


def log_request_post(prompt: str, url: str, _json: dict) -> (requests.Response, str | dict | list):
    res = requests.post(url, json=_json)
    print(f'DEBUG-{prompt}-REQUEST-JSON', _json)
    return log_request(prompt, res)


def log_request_patch(prompt: str, url: str, _json: dict) -> (requests.Response, str | dict | list):
    res = requests.patch(url, json=_json)
    print(f'DEBUG-{prompt}-REQUEST-JSON', _json)
    return log_request(prompt, res)


def log_request_delete(prompt: str, url: str) -> (requests.Response, str | dict | list):
    res = requests.delete(url)
    return log_request(prompt, res)


def error(request, user, message):
    return render(request, 'blog/error.html', {'user': user, 'error': message})


def unauthorized(request, user):
    return error(request, user, 'Access token expired, please re-login')


def get_auth_tokens(form: LoginForm) -> (requests.Response, str | dict | list):
    return log_request_post(
        'GET-AUTH-TOKENS',
        f'{ServiceUrl.SESSION}/api/token/',
        create_json_from_form(form, ['username', 'password'])
    )


def set_auth_tokens(response: HttpResponse, tokens: dict):
    response.set_cookie('access_token', tokens['access'], httponly=True)
    response.set_cookie('refresh_token', tokens['refresh'], httponly=True)


def get_auth_user(request: HttpRequest) -> dict:
    access_token = request.COOKIES.get('access_token')
    if access_token is None:
        return {'is_authenticated': False}
    res, _json = log_request_post(
        'GET-AUTH-USER-BY-TOKEN',
        f'{ServiceUrl.GATEWAY}/api/v1/user-by-token/',
        {'token': access_token}
    )
    if res.status_code != status.HTTP_200_OK:
        return {'is_authenticated': False}
    return {'is_authenticated': True, **_json}


class ContextPassUserMixin:
    cached_context = None

    def get_context_data(self, **kwargs):
        if self.cached_context is None:
            self.cached_context = super().get_context_data(**kwargs)
            self.cached_context['user'] = get_auth_user(self.request)
        return self.cached_context


class LoginRequiredMixin(ContextPassUserMixin):
    is_authenticated = True

    def render_error(self):
        return error(self.request, self.cached_context['user'], 'You must be logged in to see this page')

    def render_to_response(self, context, **kwargs):
        if context['user']['is_authenticated'] != self.is_authenticated:
            return self.render_error()
        return super().render_to_response(context, **kwargs)


class GuestRequiredMixin(LoginRequiredMixin):
    is_authenticated = False

    def render_error(self):
        return error(self.request, self.cached_context['user'], 'You are already logged in')


def add_error_in_form(form, data):
    form.add_error(None, data.get('detail', data))


class LoginFormTemplateView(GuestRequiredMixin, FormView):
    success_url = reverse_lazy('blog:publications')

    def form_valid(self, form: LoginForm) -> HttpResponse:
        res, _json = get_auth_tokens(form)
        if res.status_code != status.HTTP_200_OK:
            add_error_in_form(form, _json)
            return super().form_invalid(form)
        ret = super().form_valid(form)
        set_auth_tokens(ret, _json)
        return ret


class LoginView(LoginFormTemplateView):
    template_name = 'blog/login.html'
    form_class = LoginForm


class CheckStatusMixin:
    def check_status(self, res: requests.Response, _status: int, _json, form: forms.Form):
        if res.status_code != _status:
            add_error_in_form(form, _json)
            return super().form_invalid(form)
        return super().form_valid(form)


class RegisterView(CheckStatusMixin, LoginFormTemplateView):
    template_name = 'blog/register.html'
    form_class = RegisterForm

    def form_valid(self, form: RegisterForm) -> HttpResponse:
        data = create_json_from_form(form, ['username', 'password', 'first_name', 'last_name', 'email'])
        res, _json = log_request_post('POST-USER', f'{ServiceUrl.GATEWAY}/api/v1/users/', data)
        return self.check_status(res, status.HTTP_201_CREATED, _json, form)  # call LoginFormTemplateView.form_valid


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
        res, _json = log_request_post('POST-PUBLICATION', f'{ServiceUrl.GATEWAY}/api/v1/publications/', data)
        return self.check_status(res, status.HTTP_201_CREATED, _json, form)

    def get_success_url(self):
        return reverse_lazy('blog:user_publications', args=[self.get_context_data()["user"]["username"]])


class ManipulateMixinBase(CheckStatusMixin, LoginRequiredMixin):
    obj = None

    def insert_object_in_context(self, data):
        self.cached_context['object'] = data

    def get_context_data(self, **kwargs):
        if self.cached_context is None:
            self.cached_context = super().get_context_data(**kwargs)
            res, _json = log_request_get(
                f'GET-{self.obj.upper()}',
                f'{ServiceUrl.GATEWAY}/api/v1/{self.obj}s/{self.cached_context["view"].kwargs["pk"]}/'
            )
            self.cached_context['request_status'] = res.status_code
            self.insert_object_in_context(_json)
        return self.cached_context

    def get_author_uid(self, context):
        return context['object']['author_uid']

    def render_to_response(self, context, **kwargs):
        if not context['user']['is_authenticated']:
            return unauthorized(self.request, context['user'])
        if context['request_status'] != status.HTTP_200_OK:
            return error(self.request, context['user'], f'Bad request: {context["object"]}')
        if self.get_author_uid(context) != context['user']['id']:
            return error(self.request, context['user'], f'Can\'t manipulate {self.obj} of other user')
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
        res, _json = log_request_patch('PATCH-PUBLICATION', url, create_json_from_form(form, ['title', 'tags', 'body']))
        return self.check_status(res, status.HTTP_200_OK, _json, form)

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
        res, _json = log_request_delete('DELETE-PUBLICATION', url)
        return self.check_status(res, status.HTTP_204_NO_CONTENT, _json, form)


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
        res, _json = log_request_post('CREATE-COMMENT', f'{ServiceUrl.GATEWAY}/api/v1/comments/', data)
        return self.check_status(res, status.HTTP_201_CREATED, _json, form)

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
        res, _json = log_request_patch('PATCH-COMMENT', url, create_json_from_form(form, ['body']))
        return self.check_status(res, status.HTTP_200_OK, _json, form)


class CommentDeleteView(CommentManipulateMixin, FormView):
    template_name = 'blog/confirm-delete.html'
    form_class = EmptyForm

    def form_valid(self, form) -> HttpResponse:
        if not get_auth_user_or_add_form_error(self.request, form):
            return super().form_invalid(form)

        res, _json = log_request_delete(
            'DELETE-COMMENT',
            f'{ServiceUrl.GATEWAY}/api/v1/comments/{self.get_context_data()["view"].kwargs["pk"]}/'
        )
        return self.check_status(res, status.HTTP_204_NO_CONTENT, _json, form)


def set_page_params(params):
    params['page'] = params.get('page', 1)
    params['page_size'] = params.get('page_size', 10)


def paginated_request_get(prompt: str, request: HttpRequest, url: str) -> (requests.Response, dict | list | str):
    params = request.GET.copy()
    set_page_params(params)
    return log_request_get(prompt, url, params)


def publications_view(request: HttpRequest) -> HttpResponse:
    res, _json = paginated_request_get('GET-PUBLICATIONS', request, f'{ServiceUrl.GATEWAY}/api/v1/publications/')
    if res.status_code != status.HTTP_200_OK:
        if res.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            error(request, get_auth_user(request), 'Publication service is unavailable')
        error(request, get_auth_user(request), f'{res.status_code}: {_json}')
    return render(request, 'blog/publication-list.html', {'user': get_auth_user(request), 'response': _json})


def check_subscribed(follower_uid, following_uid, return_subscription_uid=False):
    res, _json = log_request_get(
        'CHECK-SUBSCRIBED',
        f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/',
        {
            'follower_uid': follower_uid,
            'following_uid': following_uid,
        }
    )

    subscribed = None
    if res.status_code == status.HTTP_200_OK:
        subscribed = len(_json) > 0
        if subscribed and return_subscription_uid:
            subscribed = _json[0]['subscription_uid']

    return subscribed


def get_user_by_username(username: str):
    res, _json = log_request_get('GET-USER-BY-USERNAME', f'{ServiceUrl.GATEWAY}/api/v1/users/?username={username}')
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(_json)
    if len(_json) == 0:
        return None
    return _json[0]


def get_tag_by_name(name: str):
    res, _json = log_request_get('GET-TAG-BY-NAME', f'{ServiceUrl.GATEWAY}/api/v1/tags/{name}/')
    if res.status_code != status.HTTP_200_OK:
        if res.status_code == status.HTTP_404_NOT_FOUND:
            return {}
        print(res)
        raise Exception(_json)
    return _json


def blog_view(request: HttpRequest, username: str) -> HttpResponse:
    user = get_user_by_username(username)
    if user is None:
        return HttpResponseNotFound(f'User with username "{username}" not found')

    auth_user = get_auth_user(request)

    subscribed = None
    if auth_user['is_authenticated'] and auth_user['username'] != username:
        subscribed = check_subscribed(auth_user['id'], user['id'])

    res, _json = paginated_request_get(
        'GET-USER-PUBLICATIONS',
        request,
        f'{ServiceUrl.GATEWAY}/api/v1/publications/?author_uid={user["id"]}'
    )
    if res.status_code != status.HTTP_200_OK:
        print(res)
        raise Exception(_json)
    return render(request, 'blog/publication-list.html', {
        'user': auth_user,
        'author_uid': user['id'],
        'username': user['username'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'response': _json,
        'subscribed': subscribed,
    })


def publication_view(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    auth_user = get_auth_user(request)
    if auth_user['is_authenticated'] and auth_user['is_superuser']:
        return statistics_view(request, pk, auth_user)

    viewer_uid = f'?viewer_uid={auth_user["id"]}' if auth_user['is_authenticated'] else ''
    res, _json = paginated_request_get(
        'GET-PUBLICATION',
        request,
        f'{ServiceUrl.GATEWAY}/api/v1/publications/{pk}/{viewer_uid}'
    )
    if res.status_code != status.HTTP_200_OK:
        if res.status_code == status.HTTP_404_NOT_FOUND:
            return error(request, auth_user, f'Publication with uuid {pk} not found')
        if res.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            return error(request, auth_user, f'Publication service is unavailable')
        print(res, _json)
        raise Exception(_json)
    return render(request, 'blog/publication.html', {'user': auth_user, 'response': _json})


def statistics_view(request: HttpRequest, pk: uuid.UUID, user) -> HttpResponse:
    res, _json = paginated_request_get(
        'GET-STATISTICS',
        request,
        f'{ServiceUrl.GATEWAY}/api/v1/statistics/{pk}/'
    )
    if res.status_code != status.HTTP_200_OK:
        return error(request, user, 'Statistics service is unavailable')
    return render(request, 'blog/publication.html', {'user': user, 'response': _json})


class VoteView(View):
    content_type = None
    value = None

    def post(self, request, pk: uuid.UUID):
        user = get_auth_user(request)
        res, _json = log_request_post(
            'POST-VOTE',
            f'{ServiceUrl.GATEWAY}/api/v1/vote/',
            {
                'value': self.value,
                'user_uid': user['id'],
                'content_type': self.content_type,
                'object_id': str(pk),
            }
        )
        if res.status_code != status.HTTP_200_OK:
            if res.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
                return error(request, user, f'Publication service is unavailable: {_json}')
            print(res)
            raise Exception(_json)

        return HttpResponse(content=res.content, content_type="application/json")


def tag_view(request: HttpRequest, tag: str) -> HttpResponse:
    auth_user = get_auth_user(request)

    subscribed = None
    if auth_user['is_authenticated']:
        res, _json = log_request_get('GET-TAG', f'{ServiceUrl.GATEWAY}/api/v1/tags/{tag}/')
        if res.status_code != status.HTTP_200_OK:
            if res.status_code == status.HTTP_404_NOT_FOUND:
                return error(request, auth_user, f'Tag {tag} not found')
            if res.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
                return error(request, auth_user, f'Publication service is unavailable')
            print(res)
            raise Exception(_json)
        tag_uid = _json['id']
        subscribed = check_subscribed(auth_user['id'], tag_uid)

    res, _json = paginated_request_get(
        'GET-PUBLICATIONS-BY-TAG',
        request,
        f'{ServiceUrl.GATEWAY}/api/v1/publications/?tags__name={tag}'
    )
    if res.status_code != status.HTTP_200_OK:
        if res.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            return error(request, auth_user, f'Publication service is unavailable')
        print(res)
        raise Exception(_json)
    return render(request, 'blog/publication-list.html', {
        'user': auth_user,
        'tag': tag,
        'response': _json,
        'subscribed': subscribed,
    })


def feed_view(request: HttpRequest) -> HttpResponse:
    user = get_auth_user(request)
    if not user['is_authenticated']:
        return error(request, user, 'You must be logged in to see this page')

    res, _json = log_request_get(
        'GET-SUBSCRIPTIONS-BY-FOLLOWER-UID',
        f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/?follower_uid={user["id"]}'
    )
    if res.status_code != status.HTTP_200_OK:
        return error(request, user, 'Subscription service is unavailable')

    authors = []
    tags = []
    for sub in _json:
        if sub['type'] == 'user':
            authors.append(sub['following_uid'])
        elif sub['type'] == 'tag':
            tags.append(sub['following_uid'])

    params = request.GET.copy()
    set_page_params(params)
    params['author_uid__in'] = ','.join(authors)
    params['tags__id__in'] = ','.join(tags)
    res, _json = log_request_get(
        'GET-PUBLICATIONS-BY-SUBSCRIPTIONS',
        f'{ServiceUrl.GATEWAY}/api/v1/publications/',
        params
    )
    if res.status_code != status.HTTP_200_OK:
        return error(request, user, 'Publication service is unavailable')
    return render(request, 'blog/publication-list.html', {'user': user, 'response': _json})


class Subscribe(View):
    obj = None
    subscribe = None

    def get(self, request, obj_name: str):
        follower = get_auth_user(request)
        if not follower['is_authenticated']:
            return error(request, follower, 'You must be logged in to see this page')

        following = {}
        if self.obj == 'user':
            try:
                following = get_user_by_username(obj_name)
            except Exception:
                return error(request, follower, 'Session service is unavailable')
        elif self.obj == 'tag':
            try:
                following = get_tag_by_name(obj_name)
            except Exception:
                return error(request, follower, 'Publication service is unavailable')

        subscribed = check_subscribed(follower['id'], following.get('id', ''), True)
        if bool(subscribed) == self.subscribe:
            return error(request, follower, f'Already {"un" * (not self.subscribe)}subscribed')

        if self.subscribe:
            res, _json = log_request_post(
                'POST-SUBSCRIPTION',
                f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/',
                {
                    'follower_uid': follower['id'],
                    'following_uid': following['id'],
                    'type': self.obj,
                }
            )
            if res.status_code != status.HTTP_201_CREATED:
                return error(request, follower, f'Bad request: {_json}')
        else:
            res, _json = log_request_delete(
                'DELETE-SUBSCRIPTION',
                f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/{subscribed}/'
            )
            if res.status_code != status.HTTP_204_NO_CONTENT:
                if res.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
                    return error(request, follower, 'Subscription service is unavailable')
                return error(request, follower, f'{res.status_code}: {_json}')

        return redirect('blog:user_publications' if self.obj == 'user' else 'blog:tag', obj_name)


def subscriptions(request: HttpRequest) -> HttpResponse:
    user = get_auth_user(request)
    if not user['is_authenticated']:
        return error(request, user, 'You must be logged in to see this page')

    res, _json = log_request_get(
        'GET-SUBSCRIPTIONS-BY-FOLLOWER-UID',
        f'{ServiceUrl.GATEWAY}/api/v1/subscriptions/?follower_uid={user["id"]}'
    )
    if res.status_code != status.HTTP_200_OK:
        return error(request, user, 'Subscription service is unavailable')

    authors = []
    tags = []
    for sub in _json:
        if sub['type'] == 'user':
            authors.append(sub['following_uid'])
        elif sub['type'] == 'tag':
            tags.append(sub['following_uid'])

    users = []
    for author in authors:
        res, _json = log_request_get('GET-USER-BY-UID', f'{ServiceUrl.GATEWAY}/api/v1/users/{author}/')
        if res.status_code != status.HTTP_200_OK:
            return error(request, user, 'Session service is unavailable')
        users.append(_json)

    tag_names = []
    for tag in tags:
        res, _json = log_request_get('GET-TAG-BY-UID', f'{ServiceUrl.GATEWAY}/api/v1/tags_uid/{tag}/')
        if res.status_code != status.HTTP_200_OK:
            return error(request, user, 'Publication service is unavailable')
        tag_names.append(_json)

    return render(request, 'blog/subscriptions.html', {'user': user, 'users': users, 'tags': tag_names})
