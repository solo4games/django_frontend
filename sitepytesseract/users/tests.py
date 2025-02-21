from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from .views import LoginUser, LogoutUser
from .forms import UserLoginForm


class UserLoginTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', email='<EMAIL>', password='<PASSWORD>')

    def setUp(self):
        self.factory = RequestFactory()
        self.view = LoginUser()
        self.form = UserLoginForm(data={'username': 'testuser', 'password': '<PASSWORD>'})

        self.assertTrue(self.form.is_valid())
        request = self.factory.post('login/')
        request.user = self.user
        self.view.request = request

        session = self.client.session
        request.session = session

    @patch('requests.post')
    def test_negative_login(self, mock_post):
        mock_post.return_value = MagicMock(status_code=400, json=lambda: {'detail': 'Test Negative Login'})

        response = self.view.form_valid(self.form)

        self.assertEqual(response.status_code, 400)

    @patch('requests.post')
    def test_positive_login(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {'access': 'Token Access Test',
                                                                          'refresh': 'Token Refresh Test'})

        response = self.view.form_valid(self.form)

        self.assertEqual(response.cookies['access_token'].value, 'Token Access Test')
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['access_token']['secure'])

        self.assertEqual(response.cookies['refresh_token'].value, 'Token Refresh Test')
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['secure'])

        self.assertEqual(response.status_code, 302)


class UserLogoutTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', email='<EMAIL>', password='<PASSWORD>')

    def setUp(self):
        self.factory = RequestFactory()
        self.view_login = LoginUser()
        self.form = UserLoginForm(data={'username': 'testuser', 'password': '<PASSWORD>'})

        self.assertTrue(self.form.is_valid())
        request = self.factory.post('login/')
        request.user = self.user
        self.view_login.request = request

        session = self.client.session
        request.session = session

        self.view_logout = LogoutUser()

    @patch('requests.post')
    def test_positive_logout(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {'access': 'Token Access Test',
                                                                          'refresh': 'Token Refresh Test'})

        response = self.view_login.form_valid(self.form)
        request = self.factory.get('logout/')
        request.session = self.client.session
        request.COOKIES['access_token'] = response.cookies['access_token']
        request.COOKIES['refresh_token'] = response.cookies['refresh_token']
        self.view_logout.request = request

        response = self.view_logout.dispatch(request)

        bad_access_token = response.cookies.get('access_token')
        bad_refresh_token = response.cookies.get('refresh_token')
        self.assertEqual(bad_access_token.value, '')
        self.assertEqual(bad_refresh_token.value, '')

        self.assertEqual(response.status_code, 302)




# Create your tests here.
