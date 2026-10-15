from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from operations.models import MenuKatering


class CateringUploadTests(APITestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        settings = override_settings(MEDIA_ROOT=self.media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        user = get_user_model().objects.create_user("catering-admin")
        user.groups.add(Group.objects.get(name="Administration"))
        self.client.force_authenticate(user)

    def image(self):
        content = BytesIO()
        Image.new("RGB", (2, 2), "yellow").save(content, format="JPEG")
        return SimpleUploadedFile("Foto Menu.JPG", content.getvalue(), content_type="image/jpeg")

    def test_photo_only_can_be_created_read_and_replaced(self):
        response = self.client.post("/api/v1/menu-katering/", {
            "tanggal": "2026-10-15", "keterangan": "", "gambar": self.image(),
        }, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        menu = MenuKatering.objects.get(pk=response.data["id"])
        self.assertTrue(menu.gambar.storage.exists(menu.gambar.name))
        self.assertIn("/media/katering/", response.data["gambar_url"])
        edited = self.client.patch(f"/api/v1/menu-katering/{menu.pk}/", {"gambar": self.image()}, format="multipart")
        self.assertEqual(edited.status_code, 200, edited.data)
        self.assertEqual(self.client.get(f"/api/v1/menu-katering/{menu.pk}/").data["gambar_url"], edited.data["gambar_url"])

    def test_empty_menu_and_invalid_image_are_rejected(self):
        empty = self.client.post("/api/v1/menu-katering/", {"tanggal": "2026-10-15", "keterangan": "   "}, format="multipart")
        self.assertEqual(empty.status_code, 400)
        invalid = self.client.post("/api/v1/menu-katering/", {
            "tanggal": "2026-10-15", "gambar": SimpleUploadedFile("bad.jpg", b"not-an-image", content_type="image/jpeg"),
        }, format="multipart")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(MenuKatering.objects.count(), 0)
