from django.contrib import admin

from apps.models import Category, Student, Ball


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    pass


@admin.register(Ball)
class BallAdmin(admin.ModelAdmin):
    pass
