from django.contrib.auth.views import LoginView
from django.urls.base import reverse_lazy
from django.views.generic.edit import CreateView

from users.forms import UserLoginForm, UserRegistrationForm


# Create your views here.

class LoginUser(LoginView):
    template_name = 'users/login.html'
    form_class = UserLoginForm
    extra_context = {
        'title': 'Авторизация',
    }

class RegisterUser(CreateView):
    template_name = 'users/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:login')
    extra_context = {
        'title': 'Регистрация'
    }