from rest_framework import serializers
from .models import File, ExtractedData
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)

from django.conf import settings

from celery import group
from .tasks import process_file


class AzureBlobFileField(serializers.FileField):
    def to_representation(self, value):
        if value is None:
            return None
        blob_url = f"{settings.BASE_URL}/api/files/media/{value.name.split('/')[1]}/{value.name.split('/')[-1]}"
        return blob_url


class FileSerializer(TaggitSerializer, serializers.ModelSerializer):
    group_name = serializers.CharField(source = 'group.name', read_only = True)
    created_by = serializers.HiddenField(default = serializers.CurrentUserDefault())
    created_by_username = serializers.CharField(source = 'created_by.username', read_only = True)
    tags = TagListSerializerField()
    file = AzureBlobFileField()
    extracted_data = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = "__all__"

    def get_extracted_data(self, obj):

        visible_data = [item for item in obj.extracted_data.all() if not item.hidden_from_user]

        return ExtractedDataSerializer(visible_data, many = True).data


class MultiFileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )
    tags = serializers.CharField(max_length = 2000, required = False)
    ai_enabled = serializers.BooleanField(default = False)

    def create(self, validated_data):
        files = validated_data.pop('files')
        user_group = self.context["group"]
        tags = validated_data.get('tags', '').split(',')
        ai_enabled = validated_data.get('ai_enabled')
        uploaded_by = self.context['request'].user

        if not group:
            raise serializers.ValidationError("You need to add a group in query params !")

        file_instances = [File.objects.create(file = file, group_id = user_group, uploaded_by = uploaded_by) for file in files]

        task_group = group(process_file.s(file.id, tags, ai_enabled) for file in file_instances)
        result = task_group.apply_async()
        return file_instances

    def update(self, instance, validated_data):
        pass


class FileListSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source = 'group.name', read_only = True)
    file = AzureBlobFileField()

    class Meta:
        model = File
        fields = "__all__"


class ExtractedDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExtractedData
        exclude = ('file', 'hidden_from_user')


class FilePartialUpdateSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = File
        fields = ['id', 'name', 'tags', 'short_description']
        read_only_fields = ['id']