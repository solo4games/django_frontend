import requests
from django.core.files.uploadedfile import UploadedFile

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic.base import View

from users.views import LogoutUser

base_url = 'http://proxi:8002/api/v1'

def api_upload(file: UploadedFile):
    response = requests.post(base_url + '/upload_doc/', files={'file': file})
    return response

def api_delete(file_id: int):
    response = requests.delete(base_url + '/doc_delete/', params={'file_id': file_id})
    return response

def api_analyze(file_id: int):
    response = requests.post(base_url + '/doc_analyze/', params={'file_id': file_id})
    return response

def api_get_text(file_id: int):
    response = requests.get(base_url + '/get_text/', params={'file_id': file_id})
    return response

def api_error_handler(status_code, message):
    context_error = {'status_code': status_code, 'message': message}
    html = render_to_string('docs_analyze/error_message.html', context_error)
    return HttpResponse(html, status=status_code)

class JWTView(View):

    def assigning_access_token(self, jwt_proxi_json, response):
        response.set_cookie('access_token', jwt_proxi_json['access'],
                            httponly=True, secure=True, samesite='Lax')

    def logout_user(self, request):
        logout_view = LogoutUser.as_view()
        logout_view(request)

    def verify_jwt_token(self, token):
        verify_response = requests.post(base_url + '/token/verify/', json={'token': token})
        return True if verify_response.status_code == 200 else False

    def check_jwt(self, access_token, refresh_token):
        access_bool = self.verify_jwt_token(access_token)
        refresh_bool = self.verify_jwt_token(refresh_token)

        if not refresh_token:
            return api_error_handler(500, 'Something went wrong on our server')

        if not access_bool and not refresh_bool:
            return api_error_handler(401, 'Please log in.')

    def dispatch(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        access_token = request.COOKIES.get('access_token')

        jwt_errors = self.check_jwt(access_token, refresh_token)
        if jwt_errors:
            self.logout_user(request)
            return jwt_errors

        jwt_proxi_response = requests.post(base_url + '/token/refresh/',
                                           json={'refresh': refresh_token})
        jwt_data = jwt_proxi_response.json()
        if jwt_proxi_response.status_code != 200:
            self.logout_user(request)
            return api_error_handler(jwt_proxi_response.status_code, 'Something went wrong on our server')
        response = super().dispatch(request, *args, **kwargs)
        self.assigning_access_token(jwt_data, response)

        return response

