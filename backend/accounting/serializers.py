from rest_framework import serializers
from django.db import transaction
from .services import can_finance_post

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

    class Meta:
        model = MsCoa
        fields = ["kode_akun", "sub_golongan", "nama_akun", "posisi_normal", "is_active"]


class MsPeriodeAkuntansiSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsPeriodeAkuntansi
        fields = ["id", "kode", "tgl_mulai", "tgl_selesai", "status"]
        read_only_fields = ["status"]


class TrAnggaranSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrAnggaran
        fields = [
            "id", "kode_akun", "tahun_anggaran", "bulan",
            "nominal_anggaran", "keterangan", "carry_over", "periode",
        ]


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
