"""API operasional, dipecah per domain. Re-export viewset agar import lama jalan."""

from .students import (
    JenjangViewSet,
    KehadiranSiswaViewSet,
    KelompokViewSet,
    SiswaViewSet,
)
from .staff import AbsenPegawaiViewSet, PegawaiViewSet
from .school_services import (
    ArmadaJemputanViewSet,
    MenuKateringViewSet,
    PendaftaranJemputanViewSet,
)
from .billing import TagihanViewSet
from .payroll import GajiPegawaiViewSet, PinjamanPegawaiViewSet
from .assets import FixedAssetViewSet
from .activities import KegiatanViewSet
from .registration import PendaftaranSiswaViewSet

__all__ = [
    "JenjangViewSet", "KelompokViewSet", "SiswaViewSet", "KehadiranSiswaViewSet",
    "PegawaiViewSet", "AbsenPegawaiViewSet",
    "MenuKateringViewSet", "ArmadaJemputanViewSet", "PendaftaranJemputanViewSet",
    "TagihanViewSet",
    "PinjamanPegawaiViewSet", "GajiPegawaiViewSet",
    "FixedAssetViewSet",
    "KegiatanViewSet",
    "PendaftaranSiswaViewSet",
]
