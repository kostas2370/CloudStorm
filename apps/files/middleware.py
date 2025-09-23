import os
import re
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.http import JsonResponse


class VirusScanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".svg",
            ".webp",
            ".jfif",
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".flv",
            ".wmv",
            ".webm",
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".csv",
            ".mp3",
            ".wav",
            ".aac",
            ".flac",
            ".ogg",
            ".m4a",
        ]
        self.filename_regex = re.compile(r"^[\w.\- ]+$")
        self.max_size = getattr(settings, "DATA_UPLOAD_MAX_MEMORY_SIZE", 2_500_000)

    def __call__(self, request):
        try:
            if request.method in ["POST", "PUT"] and request.FILES:
                for file in request.FILES.values():
                    self._check_file(file)
            return self.get_response(request)

        except Exception as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    def _check_file(self, file):
        filename = file.name
        if not self.filename_regex.match(filename):
            raise SuspiciousFileOperation(
                f"Disallowed characters in uploaded filename: {filename}"
            )

        if ".." in filename or "/" in filename or "\\" in filename:
            raise SuspiciousFileOperation(
                f"Suspicious path traversal attempt in filename: {filename}"
            )

        _, ext = os.path.splitext(filename.lower())
        if ext not in self.allowed_extensions:
            raise SuspiciousFileOperation(
                f"File extension {ext} not allowed for upload."
            )

        if self.max_size and file.size > self.max_size:
            raise SuspiciousFileOperation(
                f"File {filename} exceeds the max size of {self.max_size} bytes."
            )
