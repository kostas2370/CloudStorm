from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from .models import Group, GroupUser


class GroupSerializer(TaggitSerializer, serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    passcode = serializers.CharField(write_only=True, required=False)
    max_size = serializers.IntegerField(read_only=True)
    tags = TagListSerializerField(required=False)
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Group
        fields = "__all__"

    def get_members(self, obj):
        users = GroupUser.objects.filter(group_id=obj.id)
        return GroupUserSerializer(users, many=True).data

    def create(self, validated_data):
        request_user = self.context["request"].user
        group = super().create(validated_data)
        GroupUser.objects.create(
            group=group, user=request_user, role="admin", can_add=True, can_delete=True
        )
        return group


class GroupListsSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    tags = TagListSerializerField()

    class Meta:
        model = Group
        fields = "__all__"


class GroupUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GroupUser
        exclude = ("group", "id")
