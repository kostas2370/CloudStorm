import logging
import os
import tempfile
import zipfile

from django.core.files.base import ContentFile

from .exceptions import (
    FileAlreadyGenerating,
    GenerationFailed,
    UnsupportedFileType,
)
from .models import File
from .utils.file_utils import (
    generate_filename,
    generate_short_description,
    generate_tags,
    extract_data,
)

_FIELD_GENERATORS = {
    "name": lambda obj, data: generate_filename(obj, data.get("target_format")),
    "short_description": lambda obj, data: generate_short_description(obj),
}

logger = logging.getLogger(__name__)


def zip_upload_service(validated_data, request):
    zip_file = validated_data["file"]
    tags = validated_data.get("tags", "")
    ai_enabled = validated_data.get("ai_enabled", False)

    from .serializers import MultiFileUploadSerializer

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        files = []
        for root, _, file_names in os.walk(temp_dir):
            for filename in file_names:
                file_path = os.path.join(root, filename)
                with open(file_path, "rb") as f:
                    files.append(ContentFile(f.read(), name=filename))

        serializer = MultiFileUploadSerializer(
            data={"files": files, "tags": tags, "ai_enabled": ai_enabled},
            context={"request": request, "group": request.query_params.get("group")},
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()


def ai_generate_service(obj, validated_data):
    generate_type = validated_data["type"]
    user_prompt = validated_data.get("user_prompt")

    if not obj.supports_data_extraction():
        raise UnsupportedFileType(
            f"AI generation is not supported for {obj.file_type or 'unknown'} files."
        )

    # Claim the file in a single statement so two parallel requests cannot both start.
    claimed = File.objects.filter(pk=obj.pk, status=File.FileStatus.READY).update(
        status=File.FileStatus.GENERATE
    )
    if not claimed:
        raise FileAlreadyGenerating(
            "The file is on generate status. Wait until its done!"
        )

    obj.status = File.FileStatus.GENERATE
    updated_fields = ["status"]

    try:
        if generate_type in _FIELD_GENERATORS:
            extracted_data = _FIELD_GENERATORS[generate_type](obj, validated_data)
            if not extracted_data:
                raise GenerationFailed(
                    f"Could not generate {generate_type} for this file."
                )

            setattr(obj, generate_type, extracted_data)
            updated_fields.append(generate_type)
        elif generate_type == "tags":
            extracted_data = generate_tags(obj)
            for tag in extracted_data:
                obj.tags.add(tag)
        else:
            extracted_data = extract_data(obj, user_prompt)

    except Exception:
        logger.exception(
            "AI generation of %s failed for file %s", generate_type, obj.pk
        )
        obj.status = File.FileStatus.READY
        obj.save(update_fields=["status"])
        raise

    obj.status = File.FileStatus.READY
    obj.save(update_fields=updated_fields)

    return extracted_data
