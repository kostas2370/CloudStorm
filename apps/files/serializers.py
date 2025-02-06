from rest_framework import serializers
from .models import File
from apps.groups.models import Group


class FileSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source = 'group.name', read_only = True)
    created_by = serializers.HiddenField(default = serializers.CurrentUserDefault())
    created_by_username = serializers.CharField(source = 'created_by.username', read_only = True)

    class Meta:
        model = File
        fields = "__all__"


class MultiFileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())

    def create(self, validated_data):
        files = validated_data.pop('files')
        group = validated_data.get('group')
        uploaded_by = self.context['request'].user

        file_instances = []
        for file in files:
            file_instance = File.objects.create(
                file=file,
                group=group,
                uploaded_by=uploaded_by,
            )
            file_instances.append(file_instance)

        return file_instances


class FileListSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source = 'group.name', read_only = True)

    class Meta:
        model = File
        exclude = ('file',)
