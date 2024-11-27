from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from user_app import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', views.HealthCheck, name='health'),
    path('', include('user_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
