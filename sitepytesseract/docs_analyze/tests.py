import os
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.response import HttpResponse
from django.test import TestCase, RequestFactory

from .forms import UploadDocsForm, AnalyzeDocsForm
from .models import Docs, UsersToDocs, Price, Cart
from .service_api import JWTView
from .views import DocsHome, UploadDocs, GetTextDocs, AnalyzeDocs, DeleteDocs


class JWTViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='<EMAIL>', password='<PASSWORD>')
        self.view = JWTView.as_view()

    @patch('requests.post')
    def test_verify_jwt(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        view = JWTView()
        self.assertTrue(view.verify_jwt_token("valid_token"))

    @patch('requests.post')
    def test_verify_jwt_negative(self, mock_post):
        mock_post.return_value = MagicMock(status_code=401)

        view = JWTView()
        self.assertFalse(view.verify_jwt_token("valid_token"))

    @patch('requests.post')
    def test_check_jwt(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        view = JWTView()
        response = view.check_jwt(True, "valid_token")
        self.assertEqual(response, None)

    @patch('requests.post')
    def test_check_jwt_negative_logout(self, mock_post):
        mock_post.return_value = MagicMock(status_code=401)

        view = JWTView()
        response = view.check_jwt(False, "valid_token")
        self.assertEqual(response.status_code, 401)
        self.assertIn('Please log in.', response.content.decode())

    @patch('requests.post')
    def test_check_jwt_negative_internal(self, mock_post):
        mock_post.return_value = MagicMock(status_code=401)

        view = JWTView()
        response = view.check_jwt(False, None)
        self.assertEqual(response.status_code, 500)
        self.assertIn('Something went wrong on our server', response.content.decode())

    def test_asigning_access_token(self):
        view = JWTView()
        response = HttpResponse({'message': 'response'})

        jwt_proxi = {'access': 'test_token'}
        view.assigning_access_token(jwt_proxi, response)

        self.assertEqual(response.cookies['access_token'].value, 'test_token')
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['access_token']['secure'])

    @patch('requests.post')
    @patch('docs_analyze.service_api.JWTView.check_jwt')
    @patch('docs_analyze.service_api.JWTView.logout_user')
    def test_dispatch_jwt_error(self, mock_logout_user, mock_check_jwt, mock_post):
        request = self.factory.get('/')
        request.COOKIES['access_token'] = 'test_access_token'
        request.COOKIES['refresh_token'] = 'test_refresh_token'

        mock_post.return_value = MagicMock(status_code=200)
        mock_check_jwt.return_value = MagicMock(status_code=401, message='Logging Error')
        mock_logout_user.return_value = MagicMock(status_code=200)

        response = self.view(request)
        self.assertEqual(response.status_code, 401)
        self.assertIn('Logging Error', response.message)

    @patch('requests.post')
    @patch('docs_analyze.service_api.JWTView.check_jwt')
    @patch('docs_analyze.service_api.JWTView.logout_user')
    @patch('docs_analyze.service_api.JWTView.verify_jwt_token')
    def test_dispatch_jwt_response_error(self, mock_verify_jwt, mock_logout_user, mock_check_jwt, mock_post):
        request = self.factory.get('/')
        request.COOKIES['access_token'] = 'test_access_token'
        request.COOKIES['refresh_token'] = 'test_refresh_token'

        mock_post.return_value = MagicMock(status_code=599, message='Something went wrong on our server')
        mock_check_jwt.return_value = None
        mock_logout_user.return_value = MagicMock(status_code=200)
        mock_verify_jwt.return_value = False

        response = self.view(request)
        self.assertEqual(response.status_code, 599)
        self.assertIn('Something went wrong on our server', response.content.decode())

    @patch('requests.post')
    @patch('docs_analyze.service_api.JWTView.check_jwt')
    def test_dispatch_jwt_response_refresh(self, mock_check_jwt, mock_post):
        request = self.factory.get('/some-url/')
        request.COOKIES['access_token'] = 'test_access_token'
        request.COOKIES['refresh_token'] = 'test_refresh_token'

        mock_post.side_effect = [MagicMock(status_code=401),
                                 MagicMock(status_code=200, json=lambda: {'access': 'test_access_token'})]
        mock_check_jwt.return_value = None

        response = self.view(request)
        self.assertEqual(response.cookies['access_token'].value, 'test_access_token')

    @patch('docs_analyze.service_api.JWTView.check_jwt')
    @patch('docs_analyze.service_api.JWTView.verify_jwt_token')
    def test_dispatch_jwt_response_positive(self, mock_verify, mock_check_jwt):
        request = self.factory.get('/some-url/')
        request.COOKIES['access_token'] = 'test_access_token'
        request.COOKIES['refresh_token'] = 'test_refresh_token'

        mock_check_jwt.return_value = None
        mock_verify.return_value = True

        response = self.view(request)
        self.assertEqual(response.status_code, 405)


class TestDocsHome(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = DocsHome.as_view()

    def test_positive_home(self):
        request = self.factory.get('/')

        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_negative_home(self):
        request = self.factory.post('/')

        response = self.view(request)
        self.assertEqual(response.status_code, 405)


class TestUploadDocs(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', email='<EMAIL>', password='<PASSWORD>')

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UploadDocs()
        self.client.login(username='testuser', password='<PASSWORD>')

        self.static_path = 'docs_analyze/static/docs_analyze/test_images/image_for_analyzing.png'
        self.test_path = 'media/test.png'
        with open(self.static_path, 'rb+') as file:
            file_test = SimpleUploadedFile('test.png', file.read(), content_type='image/png')
            self.form = UploadDocsForm(files={'file': file_test})


    @patch('docs_analyze.service_api.api_upload')
    def test_negative_response_upload(self, mock_upload):
        mock_upload.return_value = MagicMock(status_code=402, json=lambda: {'detail': 'Test Error'})
        self.assertTrue(self.form.is_valid())

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 402)

    @patch('docs_analyze.service_api.api_upload')
    def test_positive_response_upload(self, mock_upload):
        request = self.factory.post('/upload/')
        request.user = self.user
        self.view.request = request
        mock_upload.return_value = MagicMock(status_code=200)
        self.assertTrue(self.form.is_valid())

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 302)

        doc = Docs.objects.get(file_path=self.test_path)
        user_doc = UsersToDocs.objects.get(doc_id=doc)

        self.assertEqual(user_doc.username, self.user.username)

        self.assertTrue(os.path.isfile(self.test_path))

        os.remove(self.test_path)


class TestGetText(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', email='<EMAIL>', password='<PASSWORD>')

    def setUp(self):
        self.factory = RequestFactory()
        self.view = GetTextDocs()
        self.client.login(username='testuser', password='<PASSWORD>')

    @patch('docs_analyze.service_api.api_get_text')
    def test_negative_get_text(self, mock_get):
        mock_get.return_value = MagicMock(status_code=402, json=lambda: {'detail': 'Test Error'})
        request = self.factory.get('/doc_text/1')

        response = self.view.get(request, docs_id=1)
        self.assertEqual(response.status_code, 402)

    @patch('docs_analyze.service_api.api_get_text')
    def test_positive_get_text(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'text': 'Test Text'})
        request = self.factory.get('/doc_text/1')
        self.view.request = request

        response = self.view.get(request, docs_id=1)
        self.assertEqual(self.view.extra_context['text'], 'Test Text')
        self.assertEqual(response.status_code, 200)


class TestAnalyzeDoc(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', email='<EMAIL>', password='<PASSWORD>')
        Docs.objects.create(file_path='test.png', size=123)

    def setUp(self):
        self.factory = RequestFactory()
        self.view = AnalyzeDocs()
        self.client.login(username='testuser', password='<PASSWORD>')
        self.form = AnalyzeDocsForm(data={'payment': True})

    @patch('docs_analyze.service_api.api_analyze')
    def test_negative_create_cart_get_text(self, mock_analyze):
        mock_analyze.return_value = MagicMock(status_code=402, json=lambda: {'detail': 'Test Error'})

        self.assertTrue(self.form.is_valid())

        doc_id = 2
        request = self.factory.post(f'/doc_analyze/{doc_id}')
        self.view.request = request
        self.view.kwargs = {'doc_id': doc_id}

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 500)

    @patch('docs_analyze.service_api.api_analyze')
    def test_negative_create_cart(self, mock_analyze):
        mock_analyze.return_value = MagicMock(status_code=403, json=lambda: {'detail': 'Test Error'})

        self.assertTrue(self.form.is_valid())

        doc_id = 1
        request = self.factory.post(f'/doc_analyze/{doc_id}')
        request.user = self.user
        self.view.request = request
        self.view.kwargs = {'doc_id': doc_id}

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 500)

    @patch('docs_analyze.service_api.api_analyze')
    def test_negative_api_analyze(self, mock_analyze):
        mock_analyze.return_value = MagicMock(status_code=402, json=lambda: {'detail': 'Test Error'})

        self.assertTrue(self.form.is_valid())

        doc_id = 1
        request = self.factory.post(f'/doc_analyze/{doc_id}')
        request.user = self.user
        self.view.request = request
        self.view.kwargs = {'doc_id': doc_id}

        Price.objects.create(file_type='.png', price=12.0)

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 402)

    @patch('docs_analyze.service_api.api_analyze')
    def test_positive_api_analyze(self, mock_analyze):
        mock_analyze.return_value = MagicMock(status_code=200, json=lambda: {'detail': 'Test Pass'})

        self.assertTrue(self.form.is_valid())

        doc_id = 1
        request = self.factory.post(f'/doc_analyze/{doc_id}')
        request.user = self.user
        self.view.request = request
        self.view.kwargs = {'doc_id': doc_id}

        Price.objects.create(file_type='.png', price=12.0)

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 302)


class TestDeleteDocs(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', email='<EMAIL>', password='<PASSWORD>')
        cls.doc = Docs.objects.create(file_path='test.png', size=123)

    def setUp(self):
        self.factory = RequestFactory()
        self.view = DeleteDocs()
        self.client.login(username='testuser', password='<PASSWORD>')
        self.form = AnalyzeDocsForm(data={'payment': True})

    @patch('docs_analyze.service_api.api_delete')
    def test_negative_delete_docs(self, mock_delete):
        mock_delete.return_value = MagicMock(status_code=404, json=lambda: {'detail': 'Test Not Found'})

        self.assertTrue(self.form.is_valid())

        doc_id = 1
        request = self.factory.post(f'/doc_delete/{doc_id}')
        request.user = self.user
        self.view.request = request
        self.view.kwargs = {'pk': doc_id}

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 404)

    @patch('docs_analyze.service_api.api_delete')
    @patch('os.remove')
    @patch('os.path.exists')
    def test_negative_delete_docs(self, mock_path_exist, mock_remove, mock_delete):
        mock_delete.return_value = MagicMock(status_code=200, json=lambda: {'detail': 'Test All Good'})
        mock_path_exist.return_value = True
        mock_remove.return_value = None

        self.assertTrue(self.form.is_valid())

        doc_id = 1
        request = self.factory.post(f'/doc_delete/{doc_id}')
        request.user = self.user
        self.view.request = request
        self.view.object = self.doc
        self.view.kwargs = {'pk': doc_id}

        response = self.view.form_valid(self.form)
        self.assertEqual(response.status_code, 302)

        self.assertRaises(Docs.DoesNotExist, Docs.objects.get, size=123)

        self.assertTrue(mock_remove.called)






