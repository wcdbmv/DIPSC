from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=128)


class RegisterForm(LoginForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=254)


class PublicationForm(forms.Form):
    title = forms.CharField(max_length=255)
    tags = forms.CharField(max_length=127)
    body = forms.TextInput()


class CommentForm(forms.Form):
    body = forms.TextInput()


class EmptyForm(forms.Form):
    pass
