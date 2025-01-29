from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.uploadedfile import UploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.forms.forms import Form
from django.http.response import HttpResponseNotFound
from django.urls.base import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, DeleteView
from django.views.generic.list import ListView

from docs_analyze.models import Docs, UsersToDocs, Cart
from docs_analyze.forms import UploadDocsForm, AnalyzeDocsForm
from . import service_api


# Create your views here.

class DocsHome(ListView):
    """
       Главная страница отображения списка документов.
    """
    template_name = 'docs_analyze/index.html'
    context_object_name = 'docs'
    extra_context = {
        'title': 'Главная страница'
    }
    model = Docs


class UploadDocs(LoginRequiredMixin, FormView):
    """
        Представление для загрузки документа.
        Для загрузки необходимо быть авторизованным
    """
    form_class = UploadDocsForm
    template_name = 'docs_analyze/upload.html'
    success_url = reverse_lazy('home')
    extra_context = {
        'title': 'Добавление файла'
    }

    def form_valid(self, form: UploadDocsForm):
        """
            Обрабатывает загруженный файл, отправляет его в API и сохраняет в базу данных.
        """
        uploaded_file = form.cleaned_data['file']
        response = service_api.api_upload(uploaded_file)

        if response.status_code >= 400:
            return service_api.api_error_handler(response.status_code, response.json()['detail'])

        path = 'media/' + uploaded_file.name
        self.handled_upload_file(uploaded_file, path)

        self.docs_create(path, uploaded_file.size)

        return super().form_valid(form)

    def handled_upload_file(self, f: UploadedFile, path: str):
        """
            Сохраняет загруженный файл в указанную директорию.
        """
        with open(path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    def docs_create(self, path: str, size: int):
        """
            Создает запись о документе в базе данных и связывает его с пользователем.
        """
        doc = Docs.objects.create(file_path=path, size=size)
        doc.save()
        UsersToDocs.objects.create(username=self.request.user.username, doc_id=doc).save()


class GetTextDocs(TemplateView):
    """
        Представление для получения и отображения текста документа.
    """
    template_name = 'docs_analyze/get_text.html'
    context_object_name = 'docs_text'
    extra_context = {
        'title': 'Вывод текста'
    }
    # request WSGIRequest

    def get(self, request: WSGIRequest, *args, **kwargs):
        """
            Получает текст документа по его ID и передает его в шаблон.
        """
        doc_id = kwargs['docs_id']

        response = service_api.api_get_text(doc_id)

        if response.status_code >= 400:
            return service_api.api_error_handler(response.status_code, response.json()['detail'])

        self.extra_context['text'] = response.json().get('text')
        return super().get(request, *args, **kwargs)


class DeleteDocs(LoginRequiredMixin, DeleteView):
    """
        Представление для удаления документа.
        Для удаления необходимо быть авторизованным под админом
    """
    model = Docs
    template_name = 'docs_analyze/check_delete.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form: Form):
        """
            Удаляет документ через API и из базы данных.
        """
        doc_id = self.kwargs['pk']

        response = service_api.api_delete(doc_id)

        if response.status_code >= 400:
            return service_api.api_error_handler(response.status_code, response.json()['detail'])

        return super().form_valid(form)


class AnalyzeDocs(LoginRequiredMixin, FormView):
    """
        Представление для анализа документа.
        Для анализа необходимо быть авторизованным.
    """
    template_name = 'docs_analyze/analyze.html'
    form_class = AnalyzeDocsForm
    success_url = reverse_lazy('home')
    extra_context = {
        'title': 'Анализ картинки'
    }
    # AnalyzeDocsForm

    def form_valid(self, form: AnalyzeDocsForm):
        """
            Запускает анализ документа, добавляет его в корзину и вызывает API.
        """
        doc_id = self.kwargs['doc_id']

        doc = Docs.objects.get(id=doc_id)
        try:
            Cart.objects.all().create(user_id=self.request.user, doc_id=doc).save()
        except ValueError as e:
            return service_api.api_error_handler(500, str(e))

        response = service_api.api_analyze(doc_id)

        if response.status_code >= 400:
            return service_api.api_error_handler(response.status_code, response.json()['detail'])

        return super().form_valid(form)


def page_not_found(request, exception):
    return HttpResponseNotFound('<h1>Страница не найдена</h1>')