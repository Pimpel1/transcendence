from django.urls import path

from . import views


# API Endpoints
# -------------
# GET  /api/translations/<lang>/  : Get translation file
#
# GET  /health/                   : Health check

urlpatterns = [
    path(
        'api/translations/<str:lang>/',
        views.GetTranslation.as_view(),
        name='get-translation'
    ),
    path(
        'health/',
        views.HealthCheck.as_view(),
        name='health-check'
    )
]
