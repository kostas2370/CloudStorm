from django.contrib.auth import get_user_model
from django.db import models
from taggit.managers import TaggableManager
import os

from .utils.data_extraction import (
    video_data_extraction,
    audio_data_extraction,
    image_data_extraction,
    document_data_extraction,
)
from .utils.file_utils import content_file_name, get_file_type
import uuid
from apps.groups.models import UUIDTaggedItem
import logging

logger = logging.Logger("CloudStorm logger")


class File(models.Model):
    FILE_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("document", "Document"),
        ("audio", "Audio"),
        ("other", "Other"),
    ]

    FILE_STATUS = [("ready", "Ready"), ("generate", "Generate")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500, blank=True, null=True)
    group = models.ForeignKey(
        "groups.Group", on_delete=models.CASCADE, related_name="files"
    )
    uploaded_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager(through=UUIDTaggedItem)
    file = models.FileField(upload_to=content_file_name)
    file_type = models.CharField(
        max_length=10, choices=FILE_TYPES, blank=True, null=True
    )
    file_size = models.PositiveIntegerField(default=1)
    file_extension = models.CharField(max_length=10, blank=True, null=True)
    short_description = models.CharField(max_length=2000, blank=True, null=True)
    status = models.CharField(max_length=20, default="ready", choices=FILE_STATUS)

    def __str__(self):
        return self.name if self.name else f"File {self.id}"

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name
        if self.file:
            self.file_size = self.file.size
            self.file_extension = os.path.splitext(self.file.name)[1][1:].lower()
            self.file_type = get_file_type(self.file_extension)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    def get_meta_data(self):
        if not self.file:
            return {}

        try:
            with self.file.open("rb") as f:
                f.seek(0, os.SEEK_END)
                size_bytes = f.tell()

            attrs = {
                "File Name": self.file.name,
                "Size (KB)": round(size_bytes / 1024, 2),
                "Uploaded At": self.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Extension": self.file_extension,
                "MIME Type": self.file.file.content_type
                if hasattr(self.file.file, "content_type")
                else "unknown",
            }

            return attrs

        except Exception as e:
            logger.error(f"Error getting metadata for file {self.file.name}: {e}")
            return {"error": str(e)}

    def data_extraction(self, prompt):
        extraction_function_mapper = {
            "image": image_data_extraction,
            "document": document_data_extraction,
            "audio": audio_data_extraction,
            "video": video_data_extraction,
        }

        extraction_function = extraction_function_mapper.get(self.file_type, None)
        if extraction_function:
            return extraction_function(self, prompt)

        return None

    def create_extracted_data(self, name, data, hidden_from_user=False):
        return ExtractedData.objects.create(
            file=self, name=name, data=data, hidden_from_user=hidden_from_user
        )

    def check_user_access(self, user):
        if not self.group.is_private:
            return True

        return self.group.is_user_member(user)


class ExtractedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(
        File, on_delete=models.CASCADE, related_name="extracted_data"
    )
    name = models.CharField(max_length=100)
    extraction_date = models.DateTimeField(auto_now_add=True)
    hidden_from_user = models.BooleanField(default=False)
    data = models.TextField()

    def __str__(self):
        return f"{self.file.name}:{self.name}"
