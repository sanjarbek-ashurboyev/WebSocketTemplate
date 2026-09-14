# chat/models.py
from django.db import models
from django.db.models import Model, ImageField, ForeignKey, CASCADE, IntegerField
from django.db.models.fields import CharField


# Create your models here.

class Category(Model):
    title = CharField(max_length=255)

    def __str__(self):
        return self.title


class Student(Model):
    fullname = CharField(max_length=255)
    photo = ImageField(upload_to='students/')

    def __str__(self):
        return self.fullname


class Ball(Model):
    student = ForeignKey('apps.Student', on_delete=CASCADE, related_name='balls')
    coin = IntegerField()







