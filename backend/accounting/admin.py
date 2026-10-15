from django.contrib import admin

from .models import (
    AuditLog,
    MsCoa,
    MsGolongan,
    MsPeriodeAkuntansi,
    MsSubGolongan,
    TrAnggaran,
    TrJurnal,
    TrJurnalDetail,
)


@admin.register(MsGolongan)
class MsGolonganAdmin(admin.ModelAdmin):
    list_display = ("kode_golongan", "nama_golongan")
    search_fields = ("kode_golongan", "nama_golongan")


@admin.register(MsSubGolongan)
class MsSubGolonganAdmin(admin.ModelAdmin):
    list_display = ("kode_sub", "nama_sub", "golongan")
    search_fields = ("kode_sub", "nama_sub")


@admin.register(MsCoa)
class MsCoaAdmin(admin.ModelAdmin):
    list_display = ("kode_akun", "nama_akun", "posisi_normal", "is_active", "saldo_awal", "tanggal_saldo_awal")
    list_filter = ("posisi_normal", "is_active")
    search_fields = ("kode_akun", "nama_akun")


@admin.register(MsPeriodeAkuntansi)
class MsPeriodeAkuntansiAdmin(admin.ModelAdmin):
    list_display = ("kode", "tgl_mulai", "tgl_selesai", "status")
    list_filter = ("status",)


class TrJurnalDetailInline(admin.TabularInline):
    model = TrJurnalDetail
    extra = 0
    autocomplete_fields = ("kode_akun",)


@admin.register(TrJurnal)
class TrJurnalAdmin(admin.ModelAdmin):
    list_display = ("no_bukti", "tanggal", "status", "tipe_sumber", "is_deleted")
    list_filter = ("status", "tipe_sumber", "is_deleted")
    search_fields = ("no_bukti", "keterangan")
    date_hierarchy = "tanggal"
    inlines = [TrJurnalDetailInline]

    def get_readonly_fields(self, request, obj=None):
        # Jurnal POSTED bersifat immutable (ditegakkan trigger DB juga).
        if obj and obj.status == "POSTED":
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)


@admin.register(TrAnggaran)
class TrAnggaranAdmin(admin.ModelAdmin):
    list_display = ("kode_akun", "tahun_anggaran", "bulan", "nominal_anggaran", "carry_over")
    list_filter = ("tahun_anggaran",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("changed_at", "table_name", "action", "row_pk", "changed_by")
    list_filter = ("table_name", "action")
    search_fields = ("row_pk",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
