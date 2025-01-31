from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from taggit.managers import TaggableManager
import os
from .utils import get_file_type, content_file_name


class File(models.Model):
    FILE_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100, blank=True, null=True)
    group = models.ForeignKey("groups.Group", on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager()
    file = models.FileField(upload_to=content_file_name)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, blank = True, null = True)
    file_size = models.PositiveIntegerField(default=1)
    file_extension = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name if self.name else f"File {self.id}"

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name
        if self.file:
            self.file_size = self.file.size
            self.file_extension = os.path.splitext(self.file.name)[1][1:].lower()
            self.file_type = get_file_type(self.name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save = False)
        super().delete(*args, **kwargs)
