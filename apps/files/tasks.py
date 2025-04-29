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

logger = logging.Logger("CloudStorm logger")


@shared_task
def process_file(file_id, tags, ai_enabled):
    file_instance = File.objects.get(id=file_id)
    file_instance.status = "generate"
    file_instance.save()
    if ai_enabled:
        try:
            file_instance.name = generate_filename(file_instance)
            file_instance.short_description = generate_short_description(file_instance)
            generated_tags = generate_tags(file_instance)
            for generated_tag in generated_tags:
                file_instance.tags.add(generated_tag)
            file_instance.save()
        except Exception as exc:
            logger.error(exc)

    for tag in tags:
        if tag:
            file_instance.tags.add(tag)

    file_instance.status = "ready"
    file_instance.save()
    return file_instance.id
