import requests
from django.core.files.uploadedfile import UploadedFile

from django.http import HttpResponse
from django.template.loader import render_to_string

proxi_url = 'http://proxi:8002/api/v1/'

def api_error_handler(status_code, message):
    context_error = {'status_code': status_code, 'message': message}
    html = render_to_string('docs_analyze/error_message.html', context_error)
    return HttpResponse(html, status=status_code)

