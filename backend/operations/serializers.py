from rest_framework import serializers

from .models import Siswa, Tagihan, TagihanDetail


class SiswaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Siswa
        fields = [
            "id", "nis", "nama", "kelompok", "tanggal_lahir", "alamat",
            "nama_ayah", "kontak_ayah", "nama_ibu", "kontak_ibu",
            "spp_nominal", "status", "periode",
        ]


class TagihanDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagihanDetail
        fields = ["id", "komponen", "akun_pendapatan", "nominal"]


class TagihanSerializer(serializers.ModelSerializer):
    detail = TagihanDetailSerializer(many=True)

    class Meta:
        model = Tagihan
        fields = [
            "id", "siswa", "periode_bulan", "periode_tahun",
            "total", "status", "jurnal", "detail",
        ]
        read_only_fields = ["status", "jurnal"]

    def create(self, validated_data):
        detail_data = validated_data.pop("detail")
        tagihan = Tagihan.objects.create(**validated_data)
        for d in detail_data:
            TagihanDetail.objects.create(tagihan=tagihan, **d)
        return tagihan
