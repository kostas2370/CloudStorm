from rest_framework import serializers


class EditGroupMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.CharField(required=False)
    can_add = serializers.BooleanField(required=False)
    can_delete = serializers.BooleanField(required=False)


class AddMemberResponseSerializer(serializers.Serializer):
    message = serializers.EmailField()
