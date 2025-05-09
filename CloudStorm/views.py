from django.http import JsonResponse


def custom_404(request, exception=None):
    return JsonResponse(
        {"error": True, "message": "Endpoint not found.", "status_code": 404},
        status=404,
    )


def custom_500(request):
    return JsonResponse(
        {"error": True, "message": "Internal server error.", "status_code": 500},
        status=500,
    )
