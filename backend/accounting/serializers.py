from rest_framework import serializers

from .models import MsCoa, TrJurnal, TrJurnalDetail


class MsCoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsCoa
        fields = ["kode_akun", "nama_akun", "posisi_normal", "is_active"]


class TrJurnalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrJurnalDetail
        fields = ["id", "kode_akun", "debit", "kredit"]


class TrJurnalSerializer(serializers.ModelSerializer):
    detail = TrJurnalDetailSerializer(many=True)

    class Meta:
        model = TrJurnal
        fields = [
            "id", "no_bukti", "tanggal", "keterangan", "tipe_sumber",
            "status", "created_by", "approved_by", "posted_at", "is_deleted",
            "detail",
        ]
        read_only_fields = ["id", "status", "created_by", "approved_by", "posted_at"]

    def validate(self, attrs):
        detail = attrs.get("detail", [])
        total_debit = sum((d["debit"] for d in detail), 0)
        total_kredit = sum((d["kredit"] for d in detail), 0)
        if total_debit != total_kredit:
            raise serializers.ValidationError(
                f"Jurnal tidak seimbang (debit {total_debit} != kredit {total_kredit})."
            )
        if total_debit == 0:
            raise serializers.ValidationError("Jurnal kosong.")
        return attrs

    def create(self, validated_data):
        import uuid

        detail_data = validated_data.pop("detail")
        jurnal = TrJurnal.objects.create(
            id=uuid.uuid4(), status="DRAFT", **validated_data
        )
        for d in detail_data:
            TrJurnalDetail.objects.create(jurnal=jurnal, **d)
        return jurnal
