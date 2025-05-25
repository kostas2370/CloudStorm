class VirusScanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ["POST", "PUT"] and request.FILES:
            for file in request.FILES.values():
                print(file)

        return self.get_response(request)
