import logging
import os
import tempfile
import zipfile

from django.core.files.base import ContentFile

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

logger = logging.Logger("CloudStorm Logger")


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

    obj.status = "generate"
    obj.save(update_fields=["status"])

    try:
        extracted_data = None

        if generate_type in _FIELD_GENERATORS:
            extracted_data = _FIELD_GENERATORS[generate_type](obj, validated_data)
            setattr(obj, generate_type, extracted_data)
        elif generate_type == "tags":
            extracted_data = generate_tags(obj)
            if extracted_data:
                for tag in extracted_data:
                    obj.tags.add(tag)
        else:
            extracted_data = extract_data(obj, user_prompt)

    except Exception as exc:
        logger.error(exc)
        obj.status = "ready"
        obj.save(update_fields=["status"])
        raise

    obj.status = "ready"
    obj.save(update_fields=["status", "name", "short_description"])

    return extracted_data
