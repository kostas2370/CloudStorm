from rest_framework import serializers
from .models import File, ExtractedData
from apps.groups.models import Group
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)
from .utils.file_utils import generate_filename, generate_short_description, generate_tags

from django.conf import settings
from concurrent.futures import ThreadPoolExecutor


def process_file(file, group, uploaded_by, tags, ai_enabled):
    file_instance = File.objects.create(
        file=file,
        group=group,
        uploaded_by=uploaded_by,
    )
    if ai_enabled:
        try:
            file_instance.name = generate_filename(file_instance)
            file_instance.short_description = generate_short_description(file_instance)
            generated_tags = generate_tags(file_instance)
            for generated_tag in generated_tags:
                file_instance.tags.add(generated_tag)
            file_instance.save()
        except Exception as exc:
            print(exc)

    for tag in tags:
        if tag:
            file_instance.tags.add(tag)

    return file_instance


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
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    tags = serializers.CharField(max_length = 2000, required = False)
    ai_enabled = serializers.BooleanField(default = False)

    def create(self, validated_data):
        files = validated_data.pop('files')
        group = validated_data.get('group')
        tags = validated_data.get('tags', '').split(',')
        ai_enabled = validated_data.get('ai_enabled')
        uploaded_by = self.context['request'].user

        file_instances = []
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_file, file, group, uploaded_by, tags, ai_enabled) for file in files]
            for future in futures:
                file_instances.append(future.result())

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