from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user.

    Role/otorisasi memakai Django Groups (Finance, SchoolPrincipal,
    Administration, TeacherInCharge). Model di-custom sejak awal agar
    penambahan field/relasi (mis. link ke pegawai) di masa depan aman.
    """

    class Meta:
        db_table = "accounts_user"
