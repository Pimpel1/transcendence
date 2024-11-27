import json
import logging
import os

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from translation_service.utils.decorators import handle_exceptions, log_request
from translation_service.utils.mixins import MethodNotAllowedMixin


logger = logging.getLogger('translation-service')


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class GetTranslation(MethodNotAllowedMixin, View):
    # GET /api/translations/<lang>/ : Get translation file

    def get(self, request, *args, **kwargs):
        translations_dir = os.path.join(
            settings.BASE_DIR,
            'translation_files'
            )
        lang = kwargs.get('lang')
        default_file = os.path.join(translations_dir, 'en.json')
        requested_file = os.path.join(translations_dir, f'{lang}.json')

        if os.path.exists(requested_file):
            translation_file = requested_file
        else:
            translation_file = default_file

        if not os.path.exists(translation_file):
            return JsonResponse(
                {'error': 'Translation file not found'},
                status=404
                )

        with open(translation_file, 'r') as file:
            translation_data = json.load(file)
        return JsonResponse(translation_data)


@method_decorator(handle_exceptions, name='dispatch')
class HealthCheck(MethodNotAllowedMixin, View):
    # GET /health/ : Returns status ok

    def get(self, request):
        return JsonResponse({'status': 'ok'})
