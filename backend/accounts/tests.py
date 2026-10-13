from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APITestCase

from accounts.permissions import _in_groups

User = get_user_model()


class AccountsTests(TestCase):
    def test_custom_user_model_aktif(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")
        self.assertEqual(User._meta.db_table, "accounts_user")

    def test_seed_demo_creates_four_users(self):
        from django.core.management import call_command

        call_command("seed_demo", "--users-only", "--password", "LebahMadu2026!")
        self.assertTrue(User.objects.filter(username="admin.tu").exists())
        self.assertTrue(User.objects.filter(username="keuangan").exists())
        self.assertTrue(User.objects.filter(username="kepsek").exists())
        self.assertTrue(User.objects.filter(username="guru.kegiatan").exists())
        admin = User.objects.get(username="admin.tu")
        self.assertIn("Administration", admin.groups.values_list("name", flat=True))
        self.assertTrue(admin.check_password("LebahMadu2026!"))

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


class MeApiTests(APITestCase):
    def test_me_butuh_login(self):
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_me_mengembalikan_role(self):
        u = User.objects.create_user("u2", password="x")
        u.groups.add(Group.objects.get(name="Finance"))
        self.client.force_authenticate(u)
        r = self.client.get("/api/v1/auth/me/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["username"], "u2")
        self.assertIn("Finance", r.data["groups"])
