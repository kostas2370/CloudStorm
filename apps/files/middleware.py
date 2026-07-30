import os
import re
import zipfile
import filetype
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.http import JsonResponse

from .utils.file_utils import ALLOWED_EXTENSIONS, ARCHIVE_EXTENSIONS, get_file_type

HEADER_BYTES = 8192
DEFAULT_MAX_UPLOAD_SIZE = 100 * 1024 * 1024
DEFAULT_MAX_ARCHIVE_ENTRIES = 1000
DEFAULT_MAX_ARCHIVE_UNCOMPRESSED_SIZE = 500 * 1024 * 1024
DEFAULT_MAX_ARCHIVE_COMPRESSION_RATIO = 100

# filetype only sniffs binary formats, so text based uploads are matched on extension only.
TEXT_EXTENSIONS = frozenset({".txt", ".csv", ".svg"})

# Office documents are zip containers and are sometimes reported as a plain zip.
ZIP_BACKED_EXTENSIONS = frozenset({".docx", ".xlsx", ".pptx"})

# Anything a zip upload is allowed to be detected as.
ZIP_CONTAINER_EXTENSIONS = ZIP_BACKED_EXTENSIONS | {".zip"}


class VirusScanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_extensions = ALLOWED_EXTENSIONS
        self.filename_regex = re.compile(r"^[\w.\- ]+$")
        self.max_size = getattr(settings, "MAX_UPLOAD_SIZE", DEFAULT_MAX_UPLOAD_SIZE)
        self.max_archive_entries = getattr(
            settings, "MAX_ARCHIVE_ENTRIES", DEFAULT_MAX_ARCHIVE_ENTRIES
        )
        self.max_archive_size = getattr(
            settings,
            "MAX_ARCHIVE_UNCOMPRESSED_SIZE",
            DEFAULT_MAX_ARCHIVE_UNCOMPRESSED_SIZE,
        )
        self.max_compression_ratio = getattr(
            settings,
            "MAX_ARCHIVE_COMPRESSION_RATIO",
            DEFAULT_MAX_ARCHIVE_COMPRESSION_RATIO,
        )

    def __call__(self, request):
        if request.method in ["POST", "PUT", "PATCH"] and request.FILES:
            try:
                for file in request.FILES.values():
                    self._check_file(file)
            except SuspiciousFileOperation as exc:
                return JsonResponse(
                    {"error": str(exc)},
                    status=400,
                )

        return self.get_response(request)

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

        self._check_content(file, ext)

    def _check_content(self, file, ext):
        header = file.read(HEADER_BYTES)
        file.seek(0)

        kind = filetype.guess(header)
        if kind is None:
            if ext in TEXT_EXTENSIONS:
                return

            raise SuspiciousFileOperation(
                f"Could not verify that the content of {file.name} is a real {ext} file."
            )

        detected_ext = f".{kind.extension}"

        if ext in ARCHIVE_EXTENSIONS:
            if detected_ext not in ZIP_CONTAINER_EXTENSIONS:
                raise SuspiciousFileOperation(
                    f"Content of {file.name} is {kind.mime}, which is not a zip archive."
                )

            self._check_archive(file)
            return

        if detected_ext == ".zip" and ext in ZIP_BACKED_EXTENSIONS:
            return

        if get_file_type(kind.extension) != get_file_type(ext[1:]):
            raise SuspiciousFileOperation(
                f"Content of {file.name} is {kind.mime}, which does not match its {ext} extension."
            )

    def _check_archive(self, file):
        # Only the central directory is read here, nothing is decompressed.
        try:
            with zipfile.ZipFile(file) as archive:
                entries = [info for info in archive.infolist() if not info.is_dir()]
        except zipfile.BadZipFile:
            raise SuspiciousFileOperation(f"{file.name} is not a readable zip archive.")
        finally:
            file.seek(0)

        if len(entries) > self.max_archive_entries:
            raise SuspiciousFileOperation(
                f"{file.name} contains {len(entries)} files, the limit is {self.max_archive_entries}."
            )

        uncompressed_size = sum(info.file_size for info in entries)
        compressed_size = sum(info.compress_size for info in entries)

        if uncompressed_size > self.max_archive_size:
            raise SuspiciousFileOperation(
                f"{file.name} expands to {uncompressed_size} bytes, the limit is {self.max_archive_size} bytes."
            )

        if (
            compressed_size
            and uncompressed_size / compressed_size > self.max_compression_ratio
        ):
            raise SuspiciousFileOperation(
                f"{file.name} has a compression ratio above {self.max_compression_ratio}, it looks like a zip bomb."
            )

        for info in entries:
            self._check_archive_entry(file.name, info.filename)

    def _check_archive_entry(self, archive_name, entry_name):
        parts = entry_name.replace("\\", "/").split("/")
        if entry_name.startswith("/") or ".." in parts:
            raise SuspiciousFileOperation(
                f"{archive_name} contains an unsafe path: {entry_name}"
            )

        _, ext = os.path.splitext(parts[-1].lower())
        if ext not in self.allowed_extensions or ext in ARCHIVE_EXTENSIONS:
            raise SuspiciousFileOperation(
                f"{archive_name} contains a file that is not allowed for upload: {entry_name}"
            )
