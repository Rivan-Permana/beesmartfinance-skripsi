from rest_framework import serializers

from .models import (
    AbsenPegawai,
    ArmadaJemputan,
    FixedAsset,
    GajiPegawai,
    Jenjang,
    KehadiranSiswa,
    Kegiatan,
    Kelompok,
    MenuKatering,
    Pegawai,
    PendaftaranJemputan,
    PendaftaranSiswa,
    PinjamanPegawai,
    Siswa,
    Tagihan,
    TagihanDetail,
)


class JenjangSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jenjang
        fields = "__all__"


class KelompokSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kelompok
        fields = "__all__"


class PegawaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pegawai
        fields = [
            "id", "nip", "nama", "jabatan", "nomor_hp", "alamat",
            "status_aktif", "user",
        ]


class KehadiranSiswaSerializer(serializers.ModelSerializer):
    class Meta:
        model = KehadiranSiswa
        fields = "__all__"


class AbsenPegawaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenPegawai
        fields = "__all__"


class MenuKateringSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuKatering
        fields = "__all__"


class ArmadaJemputanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArmadaJemputan
        fields = "__all__"


class PendaftaranJemputanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendaftaranJemputan
        fields = ["id", "siswa", "armada", "harga"]


class PinjamanPegawaiSerializer(serializers.ModelSerializer):
    sisa_pinjaman = serializers.ReadOnlyField()

    class Meta:
        model = PinjamanPegawai
        fields = [
            "id", "pegawai", "tanggal_pinjaman", "jumlah_pinjaman", "tenor_bulan",
            "angsuran_per_bulan", "sudah_terbayar", "sisa_pinjaman", "jurnal",
        ]
        read_only_fields = ["jurnal"]


class GajiPegawaiSerializer(serializers.ModelSerializer):
    total_bruto = serializers.ReadOnlyField()
    total_netto = serializers.ReadOnlyField()

    class Meta:
        model = GajiPegawai
        fields = [
            "id", "pegawai", "periode_bulan", "periode_tahun",
            "gaji_pokok", "tunjangan_jabatan", "tunjangan_pengabdian",
            "transport", "bonus_insentif", "thr",
            "potongan_pinjaman", "potongan_asuransi",
            "total_bruto", "total_netto", "jurnal",
        ]
        read_only_fields = ["jurnal"]


class FixedAssetSerializer(serializers.ModelSerializer):
    penyusutan_per_bulan = serializers.ReadOnlyField()

    class Meta:
        model = FixedAsset
        fields = [
            "id", "nama", "akun_aset", "akun_akumulasi", "akun_beban_depr",
            "tanggal_perolehan", "harga_perolehan", "umur_manfaat_bulan",
            "metode", "akumulasi_penyusutan", "penyusutan_per_bulan",
        ]
        read_only_fields = ["akumulasi_penyusutan"]


class KegiatanSerializer(serializers.ModelSerializer):
    realisasi = serializers.ReadOnlyField()
    sisa_pagu = serializers.ReadOnlyField()
    rasio_utilisasi = serializers.ReadOnlyField()

    class Meta:
        model = Kegiatan
        fields = [
            "id", "nama", "akun_beban", "pagu", "penanggung_jawab",
            "tanggal_mulai", "tanggal_selesai", "status",
            "realisasi", "sisa_pagu", "rasio_utilisasi",
        ]


class PendaftaranSiswaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendaftaranSiswa
        fields = [
            "id", "nama_calon", "jenjang", "tanggal_daftar",
            "biaya_sitin", "biaya_pendaftaran", "status", "siswa",
            "jurnal_sitin", "jurnal_pendaftaran",
        ]
        read_only_fields = ["status", "siswa", "jurnal_sitin", "jurnal_pendaftaran"]


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
