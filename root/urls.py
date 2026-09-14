from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from apps.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("dashboard/", dashboard, name="dashboard"),
]

if settings.DEBUG:
    # serve uploaded student photos in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
