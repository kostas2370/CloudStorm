import io
import zipfile

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from apps.files.middleware import VirusScanMiddleware

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 20
PDF = b"%PDF-1.4\n%%EOF\n"
MP3 = b"ID3\x03\x00\x00\x00" + b"\x00" * 20
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 20
WINDOWS_EXECUTABLE = b"MZ\x90\x00\x03" + b"\x00" * 40
HTML = b"<html><script>alert(1)</script></html>"

VIEW_RESPONSE = "view response"


def docx_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return buffer.getvalue()


def zip_bytes(entries, compression=zipfile.ZIP_STORED):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return buffer.getvalue()


class VirusScanMiddlewareTestCase(SimpleTestCase):
    def middleware(self, get_response=None):
        return VirusScanMiddleware(get_response or (lambda request: VIEW_RESPONSE))

    def upload(self, filename, content, method="POST"):
        request = type("Request", (), {})()
        request.method = method
        request.FILES = {"file": SimpleUploadedFile(filename, content)}
        return self.middleware()(request)

    def assertAllowed(self, filename, content):
        self.assertEqual(self.upload(filename, content), VIEW_RESPONSE)

    def assertBlocked(self, filename, content):
        response = self.upload(filename, content)
        self.assertEqual(response.status_code, 400)
        return response.content.decode()


class AllowedUploadTests(VirusScanMiddlewareTestCase):
    def test_allows_files_whose_content_matches_their_extension(self):
        for filename, content in [
            ("photo.png", PNG),
            ("photo.jpg", JPEG),
            ("photo.jfif", JPEG),
            ("doc.pdf", PDF),
            ("song.mp3", MP3),
            ("clip.mp4", MP4),
            ("report.docx", docx_bytes()),
        ]:
            with self.subTest(filename=filename):
                self.assertAllowed(filename, content)

    def test_allows_text_based_files_that_cannot_be_sniffed(self):
        for filename, content in [
            ("notes.txt", b"just some plain text\n"),
            ("rows.csv", b"a,b,c\n1,2,3\n"),
            ("icon.svg", b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'),
        ]:
            with self.subTest(filename=filename):
                self.assertAllowed(filename, content)

    def test_leaves_the_file_rewound_for_the_view(self):
        upload = SimpleUploadedFile("photo.png", PNG)
        request = type("Request", (), {})()
        request.method = "POST"
        request.FILES = {"file": upload}

        self.middleware()(request)

        self.assertEqual(upload.read(), PNG)

    def test_skips_requests_without_files(self):
        request = type("Request", (), {})()
        request.method = "GET"
        request.FILES = {}

        self.assertEqual(self.middleware()(request), VIEW_RESPONSE)


class ContentSniffingTests(VirusScanMiddlewareTestCase):
    def test_blocks_content_from_another_file_category(self):
        error = self.assertBlocked("photo.pdf", PNG)

        self.assertIn("does not match its .pdf extension", error)

    def test_blocks_html_disguised_as_an_image(self):
        error = self.assertBlocked("photo.jpg", HTML)

        self.assertIn("Could not verify", error)

    def test_blocks_executable_disguised_as_an_image(self):
        error = self.assertBlocked("photo.png", WINDOWS_EXECUTABLE)

        self.assertIn("does not match its .png extension", error)

    def test_blocks_executable_disguised_as_a_text_file(self):
        error = self.assertBlocked("notes.txt", WINDOWS_EXECUTABLE)

        self.assertIn("does not match its .txt extension", error)


class FilenameAndSizeTests(VirusScanMiddlewareTestCase):
    def test_blocks_disallowed_extensions(self):
        error = self.assertBlocked("payload.exe", WINDOWS_EXECUTABLE)

        self.assertIn(".exe not allowed", error)

    def test_blocks_files_without_an_extension(self):
        self.assertBlocked("noext", PNG)

    def test_blocks_disallowed_characters(self):
        error = self.assertBlocked("we;rd.png", PNG)

        self.assertIn("Disallowed characters", error)

    def test_blocks_path_separators_in_the_raw_filename(self):
        # Django's UploadedFile strips directories itself, so check the raw name directly.
        raw_file = type("RawFile", (), {})()
        raw_file.size = len(PNG)
        raw_file.read = lambda size=None: PNG
        raw_file.seek = lambda offset: None

        for raw_name in [
            "../../etc/passwd.png",
            "sub/dir/photo.png",
            "back\\slash.png",
        ]:
            with self.subTest(raw_name=raw_name):
                raw_file.name = raw_name
                with self.assertRaises(SuspiciousFileOperation):
                    self.middleware()._check_file(raw_file)

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_blocks_files_over_the_max_upload_size(self):
        error = self.assertBlocked("big.png", PNG + b"\x00" * 200)

        self.assertIn("exceeds the max size of 100 bytes", error)


class ArchiveUploadTests(VirusScanMiddlewareTestCase):
    def test_allows_a_zip_of_allowed_files(self):
        archive = zip_bytes([("photo.png", PNG), ("notes.txt", b"text")])

        self.assertAllowed("batch.zip", archive)

    def test_allows_a_zip_with_nested_directories(self):
        archive = zip_bytes([("holiday/day one/photo.png", PNG)])

        self.assertAllowed("batch.zip", archive)

    def test_leaves_the_archive_rewound_for_the_view(self):
        archive = zip_bytes([("photo.png", PNG)])
        upload = SimpleUploadedFile("batch.zip", archive)
        request = type("Request", (), {})()
        request.method = "POST"
        request.FILES = {"file": upload}

        self.middleware()(request)

        self.assertEqual(upload.read(), archive)

    def test_blocks_non_zip_content_named_as_a_zip(self):
        error = self.assertBlocked("batch.zip", WINDOWS_EXECUTABLE)

        self.assertIn("is not a zip archive", error)

    def test_blocks_a_corrupt_zip(self):
        error = self.assertBlocked("batch.zip", b"PK\x03\x04" + b"\x00" * 60)

        self.assertIn("not a readable zip archive", error)

    def test_blocks_entries_with_disallowed_extensions(self):
        archive = zip_bytes([("photo.png", PNG), ("payload.exe", WINDOWS_EXECUTABLE)])

        error = self.assertBlocked("batch.zip", archive)

        self.assertIn("payload.exe", error)

    def test_blocks_nested_archives(self):
        archive = zip_bytes([("inner.zip", zip_bytes([("photo.png", PNG)]))])

        error = self.assertBlocked("batch.zip", archive)

        self.assertIn("inner.zip", error)

    def test_blocks_entries_that_escape_the_extraction_directory(self):
        archive = zip_bytes([("../../etc/photo.png", PNG)])

        error = self.assertBlocked("batch.zip", archive)

        self.assertIn("unsafe path", error)

    @override_settings(MAX_ARCHIVE_ENTRIES=1)
    def test_blocks_archives_with_too_many_entries(self):
        archive = zip_bytes([("one.png", PNG), ("two.png", PNG)])

        error = self.assertBlocked("batch.zip", archive)

        self.assertIn("the limit is 1", error)

    @override_settings(MAX_ARCHIVE_UNCOMPRESSED_SIZE=100)
    def test_blocks_archives_that_expand_past_the_size_limit(self):
        archive = zip_bytes([("notes.txt", b"a" * 500)])

        error = self.assertBlocked("batch.zip", archive)

        self.assertIn("the limit is 100 bytes", error)

    @override_settings(MAX_ARCHIVE_COMPRESSION_RATIO=10)
    def test_blocks_zip_bombs(self):
        archive = zip_bytes(
            [("notes.txt", b"\x00" * 1_000_000)], compression=zipfile.ZIP_DEFLATED
        )

        error = self.assertBlocked("batch.zip", archive)

        self.assertIn("zip bomb", error)


class ViewErrorHandlingTests(VirusScanMiddlewareTestCase):
    def test_does_not_convert_view_exceptions_into_400_responses(self):
        def get_response(request):
            raise ValueError("db exploded")

        request = type("Request", (), {})()
        request.method = "POST"
        request.FILES = {"file": SimpleUploadedFile("photo.png", PNG)}

        with self.assertRaises(ValueError):
            self.middleware(get_response)(request)
