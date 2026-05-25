from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.permissions import _in_groups

User = get_user_model()


class AccountsTests(TestCase):
    def test_custom_user_model_aktif(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")
        self.assertEqual(User._meta.db_table, "accounts_user")

    def test_role_groups_terseed(self):
        for nama in ["Finance", "SchoolPrincipal", "Administration", "TeacherInCharge"]:
            self.assertTrue(Group.objects.filter(name=nama).exists(), nama)

    def test_in_groups_helper(self):
        u = User.objects.create_user("u1", password="x")
        u.groups.add(Group.objects.get(name="Finance"))
        self.assertTrue(_in_groups(u, ("Finance",)))
        self.assertFalse(_in_groups(u, ("SchoolPrincipal",)))

    def test_superuser_lolos_semua_group(self):
        su = User.objects.create_superuser("boss", "boss@x.id", "x")
        self.assertTrue(_in_groups(su, ("Finance",)))
