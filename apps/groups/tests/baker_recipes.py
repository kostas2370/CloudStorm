from model_bakery.recipe import Recipe, seq, foreign_key

from apps.groups.models import Group, GroupUser
from apps.users.tests.baker_recipes import user_recipe

group_recipe = Recipe(
    Group,
    name=seq("Group "),
    is_private=False,
    max_size=2_000_000,
    created_by=foreign_key(user_recipe),
)

private_group_recipe = Recipe(
    Group,
    name=seq("Private Group "),
    is_private=True,
    max_size=2_000_000,
    created_by=foreign_key(user_recipe),
)


group_user_member_recipe = Recipe(
    GroupUser,
    user=foreign_key(user_recipe),
    group=foreign_key(group_recipe),
    role="member",
    can_add=False,
    can_delete=False,
    can_edit=False,
)

group_user_admin_recipe = Recipe(
    GroupUser,
    user=foreign_key(user_recipe),
    group=foreign_key(group_recipe),
    role="admin",
    can_add=True,
    can_delete=True,
    can_edit=True,
)
