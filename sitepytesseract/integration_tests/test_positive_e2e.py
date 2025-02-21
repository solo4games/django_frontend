import requests
import re

import pytest


def set_csrf(session, url):
    session.get(url)
    csrf_token_upload = session.cookies.get('csrftoken')
    assert csrf_token_upload is not None
    session.headers.update({"X-CSRFToken": csrf_token_upload})

def test_upload_docs_with_auth():
    django_url = "http://localhost:9001"

    session = requests.Session()

    register_url = f"{django_url}/users/register/"

    get_resp = session.get(register_url)
    assert get_resp.status_code == 200, f"Не удалось получить страницу регистрации, код {get_resp.status_code}"

    # <input type="hidden" name="csrfmiddlewaretoken" value="XYZ123" />
    csrf_match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', get_resp.text)
    assert csrf_match is not None, "CSRF-токен не найден на странице регистрации"
    csrf_token = csrf_match.group(1)
    session.headers.update({"X-CSRFToken": csrf_token})

    data = {
        "username": "test_user1",
        "password1": "testpass1",
        "password2": "testpass1",
    }
    resp_register = session.post(register_url, data=data)
    assert resp_register.status_code in [200, 302], f"Registration failed, code={resp_register.status_code}"

    login_url = f"{django_url}/users/login/"
    data = {
        "username": "admin",
        "password": "admin",
    }
    resp_login = session.post(login_url, data=data)
    assert resp_login.status_code in [200, 302], f"Login failed, code={resp_login.status_code}"

    cookies_dict = session.cookies.get_dict()
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())
    session.headers.update({"Cookie": cookie_header})

    assert "sessionid" in session.cookies, "Сессия не установлена после логина"

    upload_url = f"{django_url}/upload/"
    file_path = 'integration_tests/static/image_for_analyzing.png'
    set_csrf(session, upload_url)

    with open(file_path, 'rb+') as f:
        files = {
            "file": f
        }
        resp_upload = session.post(upload_url, files=files)

    assert session.cookies.get("access_token") != '', "Сессия не установлена после логина"
    assert session.cookies.get("refresh_token") != '', "Сессия не установлена после логина"

    assert resp_upload.status_code in [200, 302], f"Upload failed, code={resp_upload.status_code}"

    analyze_url = f"{django_url}/analyze_doc/1"
    set_csrf(session, analyze_url)

    resp_analyze = session.post(analyze_url, data={'payment': True})
    assert resp_analyze.status_code in [200, 302], f"Analyze failed, code={resp_analyze.status_code}"

    get_text_url = f"{django_url}/doc_text/1"

    resp_get_text = session.get(get_text_url)
    assert resp_get_text.status_code in [200, 302], f"Getting Text failed, code={resp_get_text.status_code}"

    delete_url = f"{django_url}/delete/1"
    set_csrf(session, delete_url)

    resp_delete = session.post(delete_url)
    assert resp_delete.status_code in [200, 302], f"Deleting failed, code={resp_delete.status_code}"

