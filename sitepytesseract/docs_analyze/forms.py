from django import forms

from docs_analyze.models import Cart


class UploadDocsForm(forms.Form):
    file = forms.ImageField(label='Файл')


class AnalyzeDocsForm(forms.Form):
    payment = forms.BooleanField(label='Оплата')

    class Meta:
        model = Cart
        fields = ['payment',]