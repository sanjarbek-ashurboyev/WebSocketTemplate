from rest_framework.fields import IntegerField
from rest_framework.serializers import ModelSerializer

from apps.models import Category, Student


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = 'id', 'title'


class StudentSerializer(ModelSerializer):
    ball = IntegerField(read_only=True)

    class Meta:
        model = Student
        fields = 'id', 'fullname', 'photo', 'ball'