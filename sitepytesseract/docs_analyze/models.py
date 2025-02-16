import os

from django.db import models
from django.http.response import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from . import service_api

# Create your models here.


class Docs(models.Model):

    file_path = models.CharField()
    size = models.IntegerField()

    def __str__(self):
        return f"File: {self.file_path}"

    def delete(self, *args, **kwargs):
        os.remove(str(self.file_path)) if os.path.exists(str(self.file_path)) else None
        return super().delete(*args, **kwargs)


class UsersToDocs(models.Model):

    username = models.CharField(max_length=100)
    doc_id = models.ForeignKey('Docs', on_delete=models.CASCADE)

    def __str__(self):
        return f"User: {self.username}, {self.doc_id}"


class Price(models.Model):

    file_type = models.CharField(max_length=100)
    price = models.FloatField()

    def __str__(self):
        return f"FilePrice: {self.file_type}, {self.price}"


class Cart(models.Model):

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    doc_id = models.ForeignKey('Docs', on_delete=models.CASCADE)
    order_price = models.FloatField(default=0.0)
    payment = models.BooleanField(default=False)

    def __str__(self):
        return f"Cart for {self.user_id}, {self.doc_id}"

    def save(self, *args, **kwargs):
        file_type = os.path.splitext(self.doc_id.file_path)[1]
        try:
            price = get_object_or_404(Price, file_type=file_type)
        except Http404:
            raise ValueError("Наш сайт не поддерживает такой формат файла, если это формат картинки, сообщите админу")
        self.order_price = price.price * self.doc_id.size

        super().save(*args, **kwargs)