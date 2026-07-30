from .models import File
from .utils.file_utils import (
    generate_filename,
    generate_short_description,
    generate_tags,
)
from celery import shared_task
from channels.layers import get_channel_layer
import logging

channel_layer = get_channel_layer()

logger = logging.getLogger(__name__)


@shared_task
def process_file(file_id, tags, ai_enabled):
    file_instance = File.objects.get(id=file_id)
    file_instance.status = File.FileStatus.GENERATE
    file_instance.save(update_fields=["status"])
    if ai_enabled:
        try:
            generated_name = generate_filename(file_instance)
            generated_description = generate_short_description(file_instance)

            if generated_name:
                file_instance.name = generated_name
            if generated_description:
                file_instance.short_description = generated_description

            for generated_tag in generate_tags(file_instance):
                file_instance.tags.add(generated_tag)

            file_instance.save(update_fields=["name", "short_description"])
        except Exception:
            logger.exception("AI processing failed for file %s", file_id)

    for tag in tags:
        if tag:
            file_instance.tags.add(tag)

    file_instance.status = File.FileStatus.READY
    file_instance.save(update_fields=["status"])
    return file_instance.id
