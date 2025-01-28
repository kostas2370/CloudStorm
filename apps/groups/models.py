from django.db import models
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager


class Group(models.Model):
    name = models.CharField(max_length = 40)
    is_private = models.BooleanField(default = False)
    passcode = models.CharField(max_length = 200)
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __setattr__(self, attrname, val):
        setter_func = 'setter_' + attrname
        if attrname in self.__dict__ and callable(getattr(self, setter_func, None)):
            super(Group, self).__setattr__(attrname, getattr(self, setter_func)(val))
        else:
            super(Group, self).__setattr__(attrname, val)

    def __str__(self):
        return self.name

    def setter_passcode(self, val):
        return val.upper()

    def check_passcode(self, passcode):
        if self.passcode:
            return self.passcode == passcode

        return True


class GroupUser(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete = models.CASCADE)
    group = models.ForeignKey('Group', on_delete = models.CASCADE)
    role = models.CharField(max_length = 20, choices = ROLE_CHOICES, default = "member")
    can_view = models.BooleanField(default = True)
    can_add = models.BooleanField(default= False)
    can_delete = models.BooleanField(default= False)

    def __str__(self):
        return self.user.username + self.group.name

    class Meta:
        unique_together = ('user', 'group')
