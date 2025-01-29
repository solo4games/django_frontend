from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms


class UserLoginForm(AuthenticationForm):

    username = forms.CharField(label='Логин')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ['username', 'password']


class UserRegistrationForm(UserCreationForm):

    username = forms.CharField(label='Придумайте логин')
    password1 = forms.CharField(label='Придумайте пароль')
    password2 = forms.CharField(label='Повторите пароль')

    class Meta:
        model = get_user_model()
        fields = ['username', 'password1', 'password2']