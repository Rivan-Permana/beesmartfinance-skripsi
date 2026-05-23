from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    AbsenPegawai,
    ArmadaJemputan,
    FixedAsset,
    GajiPegawai,
    Jenjang,
    KehadiranSiswa,
    Kelompok,
    MenuKatering,
    MsPostingRule,
    Pegawai,
    PendaftaranJemputan,
    PinjamanPegawai,
    Siswa,
    Tagihan,
    TagihanDetail,
)

admin.site.register(Jenjang)
admin.site.register(Kelompok)
admin.site.register(ArmadaJemputan)
admin.site.register(MenuKatering)
admin.site.register(KehadiranSiswa)
admin.site.register(AbsenPegawai)
admin.site.register(PendaftaranJemputan)


@admin.register(Siswa)
class SiswaAdmin(SimpleHistoryAdmin):
    list_display = ("nis", "nama", "kelompok", "status", "spp_nominal", "is_deleted")
    list_filter = ("status", "kelompok", "is_deleted")
    search_fields = ("nis", "nama")


@admin.register(Pegawai)
class PegawaiAdmin(SimpleHistoryAdmin):
    list_display = ("nip", "nama", "jabatan", "status_aktif", "is_deleted")
    list_filter = ("status_aktif", "is_deleted")
    search_fields = ("nip", "nama")


class TagihanDetailInline(admin.TabularInline):
    model = TagihanDetail
    extra = 0


@admin.register(Tagihan)
class TagihanAdmin(SimpleHistoryAdmin):
    list_display = ("siswa", "periode_bulan", "periode_tahun", "total", "status", "jurnal")
    list_filter = ("status", "periode_tahun")
    search_fields = ("siswa__nama",)
    inlines = [TagihanDetailInline]


@admin.register(PinjamanPegawai)
class PinjamanPegawaiAdmin(SimpleHistoryAdmin):
    list_display = ("pegawai", "tanggal_pinjaman", "jumlah_pinjaman", "sudah_terbayar")


@admin.register(GajiPegawai)
class GajiPegawaiAdmin(SimpleHistoryAdmin):
    list_display = ("pegawai", "periode_bulan", "periode_tahun", "jurnal")
    list_filter = ("periode_tahun",)


@admin.register(FixedAsset)
class FixedAssetAdmin(SimpleHistoryAdmin):
    list_display = ("nama", "harga_perolehan", "umur_manfaat_bulan", "akumulasi_penyusutan")


@admin.register(MsPostingRule)
class MsPostingRuleAdmin(admin.ModelAdmin):
    list_display = ("event_code", "komponen", "akun_debit", "akun_kredit", "aktif")
    list_filter = ("event_code", "aktif")
