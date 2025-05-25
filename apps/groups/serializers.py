from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from .models import Group, GroupUser
from django.contrib.auth import get_user_model


class GroupUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GroupUser
        exclude = ("group", "id")


class GroupSerializer(TaggitSerializer, serializers.ModelSerializer):
    members = GroupUserSerializer(source="groupuser_set", many=True, read_only=True)
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


class AddMemberSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    role = serializers.CharField(required=False)
    can_add = serializers.BooleanField(required=False)
    can_delete = serializers.BooleanField(required=False)

    def validate_user_email(self, value):
        user = get_user_model().objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("No user with this email exists.")
        return value

        group = self.context.get("group")
        if group and GroupUser.objects.filter(group=group, user=user).exists():
            raise serializers.ValidationError("User is already a member of this group.")

        return value

    def create(self, validated_data):
        group = self.context["group"]
        user = get_user_model().objects.get(email=validated_data["user_email"])

        group_user = GroupUser.objects.create(
            group=group,
            user=user,
            role=validated_data.get("role", "member"),
            can_add=validated_data.get("can_add", False),
            can_delete=validated_data.get("can_delete", False),
        )
        return group_user
