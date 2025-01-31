from rest_framework import serializers
from .models import File


class FileSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source = 'group.name', read_only = True)
    created_by = serializers.HiddenField(default = serializers.CurrentUserDefault())
    created_by_username = serializers.CharField(source = 'created_by.username', read_only = True)

    class Meta:
        model = File
        fields = "__all__"
