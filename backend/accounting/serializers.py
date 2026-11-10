from rest_framework import serializers
from django.db import transaction
from .kas import is_akun_kas
from .services import can_finance_post, periode_tertutup

from .models import (
    MsCoa,
    MsGolongan,
    MsPeriodeAkuntansi,
    MsSubGolongan,
    TrAnggaran,
    TrJurnal,
    TrJurnalDetail,
)


class MsGolonganSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsGolongan
        fields = ["id", "kode_golongan", "nama_golongan", "deskripsi"]


class MsSubGolonganSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsSubGolongan
        fields = ["id", "golongan", "kode_sub", "nama_sub"]


class MsCoaSerializer(serializers.ModelSerializer):
    sub_golongan = serializers.SlugRelatedField(
        slug_field="kode_sub",
        queryset=MsSubGolongan.objects.all(),
        allow_null=True,
        required=False,
    )

    is_kas = serializers.SerializerMethodField(help_text="Akun kas/bank yang bisa dipilih sebagai penerima atau sumber uang.")

    def get_is_kas(self, obj) -> bool:
        return is_akun_kas(obj.kode_akun, obj.nama_akun)

    def validate(self, attrs):
        if self.instance and attrs.get("kode_akun", self.instance.pk) != self.instance.pk:
            raise serializers.ValidationError({"kode_akun": "Kode akun tidak dapat diubah."})
        saldo = attrs.get("saldo_awal", getattr(self.instance, "saldo_awal", 0))
        tanggal = attrs.get("tanggal_saldo_awal", getattr(self.instance, "tanggal_saldo_awal", None))
        if saldo != 0 and tanggal is None:
            raise serializers.ValidationError({"tanggal_saldo_awal": "Isi tanggal acuan untuk saldo awal bukan nol."})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop("kode_akun", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if validated_data:
            instance.save(update_fields=list(validated_data))
        return instance

    class Meta:
        model = MsCoa
        fields = ["kode_akun", "sub_golongan", "nama_akun", "posisi_normal", "is_active", "saldo_awal", "tanggal_saldo_awal", "is_kas"]


class MsPeriodeAkuntansiSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsPeriodeAkuntansi
        fields = ["id", "kode", "tgl_mulai", "tgl_selesai", "status"]
        read_only_fields = ["status"]

    def validate(self, attrs):
        if self.instance and self.instance.status == "CLOSED":
            raise serializers.ValidationError("Periode yang sudah ditutup tidak dapat diubah.")
        mulai = attrs.get("tgl_mulai", getattr(self.instance, "tgl_mulai", None))
        selesai = attrs.get("tgl_selesai", getattr(self.instance, "tgl_selesai", None))
        if mulai and selesai:
            if mulai > selesai:
                raise serializers.ValidationError("Tanggal selesai harus sama atau setelah tanggal mulai.")
            bentrok = MsPeriodeAkuntansi.objects.filter(tgl_mulai__lte=selesai, tgl_selesai__gte=mulai)
            if self.instance:
                bentrok = bentrok.exclude(pk=self.instance.pk)
            if (lain := bentrok.first()):
                raise serializers.ValidationError(f"Rentang tanggal bertumpang tindih dengan periode {lain.kode}.")
        return attrs


class TrAnggaranSerializer(serializers.ModelSerializer):
    """Baris tanpa bulan = plafon tahunan per tahun pelajaran (wajib periode). Baris berbulan = anggaran
    bulanan; tahun_anggaran + bulan adalah bulan kalender, dan jumlahnya tidak boleh melewati plafon."""

    tahun_anggaran = serializers.IntegerField(required=False)

    class Meta:
        model = TrAnggaran
        fields = [
            "id", "kode_akun", "tahun_anggaran", "bulan",
            "nominal_anggaran", "keterangan", "carry_over", "periode",
        ]

    def validate(self, attrs):
        from datetime import date
        from decimal import Decimal

        get = lambda field: attrs.get(field, getattr(self.instance, field, None))  # noqa: E731
        akun, bulan, periode, nominal = get("kode_akun"), get("bulan"), get("periode"), get("nominal_anggaran")
        if akun is None or not akun.kode_akun.startswith("5") or not akun.is_active:
            raise serializers.ValidationError({"kode_akun": "Pilih akun beban (kode 5) yang masih aktif."})
        if nominal is None or nominal < 0:
            raise serializers.ValidationError({"nominal_anggaran": "Nominal anggaran tidak boleh negatif."})
        sama = TrAnggaran.objects.filter(kode_akun=akun)
        if self.instance:
            sama = sama.exclude(pk=self.instance.pk)
        if bulan is None:
            if periode is None:
                raise serializers.ValidationError({"periode": "Pilih tahun pelajaran untuk plafon tahunan."})
            attrs["tahun_anggaran"] = periode.tgl_mulai.year
            if sama.filter(bulan__isnull=True, periode=periode).exists():
                raise serializers.ValidationError({"kode_akun": "Plafon akun ini untuk tahun pelajaran tersebut sudah ada."})
            terpakai = sum((a.nominal_anggaran for a in sama.filter(bulan__isnull=False, periode=periode)), Decimal(0))
            if nominal < terpakai:
                raise serializers.ValidationError({
                    "nominal_anggaran": f"Plafon lebih kecil dari anggaran bulanan yang sudah disusun (Rp {terpakai:,.0f}).".replace(",", "."),
                })
            return attrs
        tahun = get("tahun_anggaran")
        if not tahun or not 1 <= bulan <= 12:
            raise serializers.ValidationError({"bulan": "Isi bulan 1–12 dan tahun anggaran."})
        if sama.filter(tahun_anggaran=tahun, bulan=bulan).exists():
            raise serializers.ValidationError({"bulan": "Anggaran akun ini untuk bulan tersebut sudah ada. Ubah baris yang ada."})
        awal = date(tahun, bulan, 1)
        periode = MsPeriodeAkuntansi.objects.filter(tgl_mulai__lte=awal, tgl_selesai__gte=awal).first()
        attrs["periode"] = periode
        plafon = sama.filter(bulan__isnull=True, periode=periode).first() if periode else None
        if plafon is not None:
            terpakai = sum((a.nominal_anggaran for a in sama.filter(bulan__isnull=False, periode=periode)), Decimal(0))
            if terpakai + nominal > plafon.nominal_anggaran:
                sisa = plafon.nominal_anggaran - terpakai
                raise serializers.ValidationError({
                    "nominal_anggaran": f"Melebihi plafon tahunan. Sisa plafon akun ini Rp {sisa:,.0f}.".replace(",", "."),
                })
        return attrs


class TrJurnalDetailSerializer(serializers.ModelSerializer):
    kode_akun = serializers.PrimaryKeyRelatedField(queryset=MsCoa.objects.filter(is_active=True))

    def validate(self, attrs):
        debit, kredit = attrs["debit"], attrs["kredit"]
        if debit < 0 or kredit < 0 or (debit > 0 and kredit > 0):
            raise serializers.ValidationError("Setiap baris hanya boleh memiliki debit atau kredit nonnegatif.")
        return attrs

    class Meta:
        model = TrJurnalDetail
        fields = ["id", "kode_akun", "debit", "kredit"]


class TrJurnalSerializer(serializers.ModelSerializer):
    detail = TrJurnalDetailSerializer(many=True)
    can_finance_post = serializers.SerializerMethodField()
    perlu_rekonsiliasi = serializers.SerializerMethodField()

    def get_can_finance_post(self, obj) -> bool:
        return can_finance_post(obj)

    def get_perlu_rekonsiliasi(self, obj) -> bool:
        if obj.tipe_sumber in {"AUTO_PENDAFTARAN", "AUTO_SITIN"}:
            from operations.services.registration import jurnal_pendaftaran_perlu_rekonsiliasi
            return jurnal_pendaftaran_perlu_rekonsiliasi(obj)
        if obj.tipe_sumber != "AUTO_BILLING":
            return False
        pembayaran = getattr(obj, "pembayaran_tagihan", None)
        return pembayaran is None or pembayaran.tagihan.perlu_rekonsiliasi

    class Meta:
        model = TrJurnal
        fields = [
            "id", "no_bukti", "tanggal", "keterangan", "tipe_sumber",
            "status", "created_by", "approved_by", "posted_at", "is_deleted",
            "detail", "can_finance_post", "perlu_rekonsiliasi",
        ]
        read_only_fields = ["id", "status", "created_by", "approved_by", "posted_at", "tipe_sumber", "is_deleted"]

    def validate(self, attrs):
        detail = attrs.get("detail")
        if detail is None:
            detail = list(self.instance.detail.values("debit", "kredit")) if self.instance else []
        total_debit = sum((d["debit"] for d in detail), 0)
        total_kredit = sum((d["kredit"] for d in detail), 0)
        if total_debit != total_kredit:
            raise serializers.ValidationError(
                f"Jurnal tidak seimbang (debit {total_debit} != kredit {total_kredit})."
            )
        if total_debit == 0:
            raise serializers.ValidationError("Jurnal kosong.")
        tanggal = attrs.get("tanggal", getattr(self.instance, "tanggal", None))
        if tanggal and (periode := periode_tertutup(tanggal)):
            raise serializers.ValidationError(
                f"Periode {periode.kode} sudah ditutup. Gunakan tanggal pada periode yang masih terbuka."
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        import uuid

        detail_data = validated_data.pop("detail")
        jurnal = TrJurnal.objects.create(
            id=uuid.uuid4(), status="DRAFT", **validated_data
        )
        for d in detail_data:
            TrJurnalDetail.objects.create(jurnal=jurnal, **d)
        return jurnal

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = TrJurnal.objects.select_for_update().get(pk=instance.pk)
        if instance.status != "DRAFT":
            raise serializers.ValidationError("Hanya jurnal DRAFT yang bisa diubah.")
        if instance.tipe_sumber != "MANUAL":
            raise serializers.ValidationError("Jurnal otomatis harus dikoreksi melalui transaksi sumbernya.")
        detail_data = validated_data.pop("detail", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if detail_data is not None:
            instance.detail.all().delete()
            for d in detail_data:
                TrJurnalDetail.objects.create(jurnal=instance, **d)
        return instance
