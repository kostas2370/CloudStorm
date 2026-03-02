from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery.recipe import Recipe, seq, foreign_key

from apps.files.models import File, ExtractedData
from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import group_recipe


file_recipe = Recipe(
    File,
    id=None,  # αφήνουμε το default uuid
    name=seq("File "),
    group=foreign_key(group_recipe),
    uploaded_by=foreign_key(user_recipe),
    # dummy in-memory file – προσοχή αν έχεις Azure storage σε tests
    file=SimpleUploadedFile("test.txt", b"dummy content", content_type="text/plain"),
    file_type="document",
    file_size=12,
    file_extension="txt",
    short_description="Test file",
    status="ready",
)


extracted_data_recipe = Recipe(
    ExtractedData,
    id=None,  # default uuid
    file=foreign_key(file_recipe),
    name=seq("Extraction "),
    hidden_from_user=False,
    data='{"key": "value"}',
)
