from rest_framework import serializers


class FileUploadResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    files = serializers.ListField(child=serializers.UUIDField())


class MassFileDeleteRequestSerializer(serializers.Serializer):
    to_delete = serializers.ListField(
        child=serializers.IntegerField(), help_text="List of file IDs to delete"
    )


class ErrorResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class ZipUploadRequestSerializer(serializers.Serializer):
    file = serializers.FileField()
    tags = serializers.CharField(required=False)
    ai_enabled = serializers.BooleanField(required=False)


class AIGenerateRequestSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=["filename", "short_description", "tags", "custom"],
        help_text="Type of AI generation task",
    )
    user_prompt = serializers.CharField(
        required=False, help_text="User prompt for custom extraction"
    )
    target_format = serializers.CharField(
        required=False, help_text="Target format for filename generation"
    )


class AIGenerateResponseSerializer(serializers.Serializer):
    extracted_data = serializers.JSONField()
