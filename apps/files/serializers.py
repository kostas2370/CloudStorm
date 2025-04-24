from rest_framework import serializers
from .models import File
from apps.groups.models import Group
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)

from django.conf import settings


class AzureBlobFileField(serializers.FileField):
    def to_representation(self, value):
        if value is None:
            return None
        blob_url = f"{settings.BASE_URL}/api/files/{value.name.split('/')[1]}/{value.name.split('/')[-1]}"
        return blob_url


class FileSerializer(TaggitSerializer, serializers.ModelSerializer):
    group_name = serializers.CharField(source = 'group.name', read_only = True)
    created_by = serializers.HiddenField(default = serializers.CurrentUserDefault())
    created_by_username = serializers.CharField(source = 'created_by.username', read_only = True)
    tags = TagListSerializerField()
    file = AzureBlobFileField()
    class Meta:
        model = File
        fields = "__all__"


class MultiFileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    tags = serializers.CharField(max_length = 2000, required = False)

    def create(self, validated_data):
        files = validated_data.pop('files')
        group = validated_data.get('group')
        tags = validated_data.get('tags', '').split(',')
        uploaded_by = self.context['request'].user
        file_instances = []

        for file in files:
            file_instance = File.objects.create(
                file=file,
                group=group,
                uploaded_by=uploaded_by,
            )

            for tag in tags:
                file_instance.tags.add(tag)

            file_instances.append(file_instance)

        return file_instances

    def update(self, instance, validated_data):
        pass


class FileListSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source = 'group.name', read_only = True)
    file = AzureBlobFileField()

    class Meta:
        model = File
        fields = "__all__"
