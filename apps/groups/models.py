from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

import uuid
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=40)
    is_private = models.BooleanField(default=False)
    tags = TaggableManager(through=UUIDTaggedItem)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_size = models.PositiveIntegerField(default=2000000)
    created_by = models.ForeignKey(
        get_user_model(), null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

    def is_user_member(self, user):
        if isinstance(user, AnonymousUser):
            return False
        return GroupUser.objects.filter(user=user, group=self).exists()


class GroupUser(models.Model):
    _ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    group = models.ForeignKey("Group", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=_ROLE_CHOICES, default="member")
    can_add = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username + self.group.name

    class Meta:
        unique_together = ("user", "group")
