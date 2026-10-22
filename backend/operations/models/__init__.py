"""Model operasional (Django ORM, fully managed), dipecah per domain.

Re-export semua model agar `from operations.models import X` & registrasi
Django tetap berfungsi seperti modul tunggal.
"""

from .base import (
    SoftDeleteManager,
    SoftDeleteModel,
    SoftDeleteQuerySet,
    TimeStampedModel,
)
from .students import Jenjang, Kelompok, KehadiranSiswa, Siswa
from .staff import AbsenPegawai, Pegawai
from .school_services import ArmadaJemputan, MenuKatering, PendaftaranJemputan, TarifKatering
from .billing import AlokasiPembayaranTagihan, KomponenBiayaTemplate, MsPostingRule, PembayaranTagihan, Tagihan, TagihanDetail
from .payroll import GajiPegawai, PinjamanPegawai, PotonganKasbonGaji
from .assets import FixedAsset
from .activities import Kegiatan, RealisasiKegiatan
from .registration import PendaftaranSiswa

__all__ = [
    "TimeStampedModel", "SoftDeleteModel", "SoftDeleteManager", "SoftDeleteQuerySet",
    "Jenjang", "Kelompok", "Siswa", "KehadiranSiswa",
    "Pegawai", "AbsenPegawai",
    "MenuKatering", "TarifKatering", "ArmadaJemputan", "PendaftaranJemputan",
    "MsPostingRule", "Tagihan", "TagihanDetail", "KomponenBiayaTemplate",
    "PembayaranTagihan", "AlokasiPembayaranTagihan",
    "PinjamanPegawai", "GajiPegawai", "PotonganKasbonGaji",
    "FixedAsset",
    "Kegiatan", "RealisasiKegiatan",
    "PendaftaranSiswa",
]
