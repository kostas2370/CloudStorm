from rest_framework import serializers
from .models import *


class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Group
        exclude = ('passcode',)

    def get_members(self, obj):
        users = GroupUser.objects.filter(group_id = obj.id)
        return GroupUserSerializer(users, many = True).data


class GroupUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source = 'user.username', read_only = True)
    class Meta:
        model = GroupUser
        fields = '__all__'
