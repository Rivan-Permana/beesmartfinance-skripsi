from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Login JWT dgn throttle 'login' (anti brute-force, 5/min)."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

from accounting.api import (
    MsCoaViewSet,
    MsGolonganViewSet,
    MsPeriodeAkuntansiViewSet,
    MsSubGolonganViewSet,
    TrAnggaranViewSet,
    TrJurnalViewSet,
)
from accounting.reports import (
    AuditLogViewSet,
    BukuBesarView,
    DashboardRingkasanView,
    LabaRugiView,
    NeracaSaldoView,
    PosisiKeuanganView,
    PrediksiKasView,
    RealisasiAnggaranView,
)
from operations.api import (
    AbsenPegawaiViewSet,
    ArmadaJemputanViewSet,
    FixedAssetViewSet,
    GajiPegawaiViewSet,
    JenjangViewSet,
    KehadiranSiswaViewSet,
    KelompokViewSet,
    MenuKateringViewSet,
    PegawaiViewSet,
    PendaftaranJemputanViewSet,
    PinjamanPegawaiViewSet,
    SiswaViewSet,
    TagihanViewSet,
)

router = DefaultRouter()
# core accounting
router.register("golongan", MsGolonganViewSet, basename="golongan")
router.register("sub-golongan", MsSubGolonganViewSet, basename="sub-golongan")
router.register("coa", MsCoaViewSet, basename="coa")
router.register("periode", MsPeriodeAkuntansiViewSet, basename="periode")
router.register("anggaran", TrAnggaranViewSet, basename="anggaran")
router.register("jurnal", TrJurnalViewSet, basename="jurnal")
router.register("audit-log", AuditLogViewSet, basename="audit-log")
# operasional sekolah
router.register("jenjang", JenjangViewSet, basename="jenjang")
router.register("kelompok", KelompokViewSet, basename="kelompok")
router.register("siswa", SiswaViewSet, basename="siswa")
router.register("kehadiran-siswa", KehadiranSiswaViewSet, basename="kehadiran-siswa")
router.register("absen-pegawai", AbsenPegawaiViewSet, basename="absen-pegawai")
router.register("menu-katering", MenuKateringViewSet, basename="menu-katering")
router.register("armada-jemputan", ArmadaJemputanViewSet, basename="armada-jemputan")
router.register("pendaftaran-jemputan", PendaftaranJemputanViewSet, basename="pendaftaran-jemputan")
router.register("tagihan", TagihanViewSet, basename="tagihan")
# kepegawaian & aset
router.register("pegawai", PegawaiViewSet, basename="pegawai")
router.register("pinjaman", PinjamanPegawaiViewSet, basename="pinjaman")
router.register("gaji", GajiPegawaiViewSet, basename="gaji")
router.register("aset", FixedAssetViewSet, basename="aset")

urlpatterns = [
    path("admin/", admin.site.urls),
    # auth (JWT)
    path("api/auth/token/", ThrottledTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # resources
    path("api/", include(router.urls)),
    # laporan & dashboard
    path("api/laporan/neraca-saldo/", NeracaSaldoView.as_view()),
    path("api/laporan/laba-rugi/", LabaRugiView.as_view()),
    path("api/laporan/posisi-keuangan/", PosisiKeuanganView.as_view()),
    path("api/laporan/realisasi-anggaran/", RealisasiAnggaranView.as_view()),
    path("api/laporan/buku-besar/<str:kode_akun>/", BukuBesarView.as_view()),
    path("api/dashboard/ringkasan/", DashboardRingkasanView.as_view()),
    path("api/dashboard/prediksi-kas/", PrediksiKasView.as_view()),
    # docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
