from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie

from matchmaker_service.utils.decorators import log_request, handle_exceptions
from matchmaker_service.utils.mixins import MethodNotAllowedMixin


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class getCsrfToken(MethodNotAllowedMixin, View):
    # GET /get-csrf-token/ : Returns CSRF token

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        csrf_token = request.META.get('CSRF_COOKIE', '')
        return JsonResponse({'csrfToken': csrf_token})


@method_decorator(handle_exceptions, name='dispatch')
class HealthCheck(MethodNotAllowedMixin, View):
    # GET /health/ : Returns status ok

    def get(self, request):
        return JsonResponse({'status': 'ok'})
