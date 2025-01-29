import requests
from django.core.files.uploadedfile import UploadedFile

from django.http import HttpResponse
from django.template.loader import render_to_string

base_url = 'http://my_project_app:8000'

def api_upload(file: UploadedFile):
    response = requests.post(base_url + '/upload_doc', files={'file': file})
    return response

def api_delete(file_id: int):
    response = requests.delete(base_url + '/doc_delete', params={'file_id': file_id})
    return response

def api_analyze(file_id: int):
    response = requests.post(base_url + '/doc_analyze', params={'file_id': file_id})
    return response

def api_get_text(file_id: int):
    response = requests.get(base_url + '/get_text', params={'file_id': file_id})
    return response

def api_error_handler(status_code, message):
    context_error = {'status_code': status_code, 'message': message}
    html = render_to_string('docs_analyze/error_message.html', context_error)
    return HttpResponse(html, status=status_code)