import requests

from django.contrib.auth.views import LoginView, LogoutView
from django.urls.base import reverse_lazy
from django.views.generic.edit import CreateView

from users.forms import UserLoginForm, UserRegistrationForm

from .utils import proxi_url, api_error_handler

# Create your views here.

class LoginUser(LoginView):
    template_name = 'users/login.html'
    form_class = UserLoginForm
    extra_context = {
        'title': 'Авторизация',
    }

    def form_valid(self, form):
        response = super().form_valid(form)

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        proxi_response = requests.post(proxi_url + 'token/',
                                      json={'username': username, 'password': password})

        if proxi_response.status_code == 200:
            proxi_json_response = proxi_response.json()
            response.set_cookie('access_token', proxi_json_response['access'],
                                httponly=True, secure=True, samesite='Lax')
            response.set_cookie('refresh_token', proxi_json_response['refresh'],
                                httponly=True, secure=True, samesite='Lax')

            return response
        else:
            return api_error_handler(proxi_response.status_code,
                                     proxi_response.json()['detail'])

class RegisterUser(CreateView):
    template_name = 'users/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:login')
    extra_context = {
        'title': 'Регистрация'
    }

class LogoutUser(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')

        return response