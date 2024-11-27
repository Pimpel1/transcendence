from django.http import JsonResponse


def mock_jwt_validate(request, username):
    request.jwt_username = username
    return JsonResponse({'message': 'Authorized'}, status=200)
