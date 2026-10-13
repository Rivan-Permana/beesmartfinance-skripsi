from decimal import Decimal

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
    jenjang_kode = serializers.CharField(source="jenjang.kode", read_only=True)
    jenjang_nama = serializers.CharField(source="jenjang.nama", read_only=True)
    siswa_aktif = serializers.SerializerMethodField()

    class Meta:
        model = Kelompok
        fields = ["id", "nama", "jenjang", "jenjang_kode", "jenjang_nama", "siswa_aktif"]

    def get_siswa_aktif(self, obj):
        return obj.siswa.filter(status="aktif").count()


class PegawaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pegawai
        fields = [
            "id", "nip", "nama", "jabatan", "nomor_hp", "alamat",
            "status_aktif", "tanggal_mulai_kerja", "tanggal_selesai_kerja", "user",
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
    gambar_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuKatering
        fields = ["id", "tanggal", "gambar", "gambar_url", "keterangan"]

    def get_gambar_url(self, obj):
        if not obj.gambar:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.gambar.url)
        return obj.gambar.url


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
    total_potongan = serializers.ReadOnlyField()
    total_netto = serializers.ReadOnlyField()

    class Meta:
        model = GajiPegawai
        fields = [
            "id", "pegawai", "periode_bulan", "periode_tahun",
            "gaji_pokok", "tunjangan_jabatan", "tunjangan_pengabdian",
            "tunjangan_asuransi", "uang_makan", "transport",
            "bonus_insentif", "thr", "hari_hadir",
            "potongan_pinjaman", "potongan_asuransi",
            "total_bruto", "total_potongan", "total_netto", "jurnal",
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
    periode_kode = serializers.CharField(source="periode.kode", read_only=True, default=None)

    class Meta:
        model = Kegiatan
        fields = [
            "id", "nama", "akun_beban", "pagu", "penanggung_jawab",
            "tanggal_mulai", "tanggal_selesai", "status", "periode", "periode_kode",
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
        fields = ["id", "komponen", "kategori", "keterangan", "akun_pendapatan", "nominal"]


class TagihanSerializer(serializers.ModelSerializer):
    detail = TagihanDetailSerializer(many=True)
    siswa_nama = serializers.CharField(source="siswa.nama", read_only=True)

    class Meta:
        model = Tagihan
        fields = [
            "id", "siswa", "siswa_nama", "periode_bulan", "periode_tahun",
            "total", "status", "jurnal", "detail",
        ]
        read_only_fields = ["status", "jurnal", "total"]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if instance and (instance.status == "LUNAS" or instance.jurnal_id):
            raise serializers.ValidationError("Tagihan lunas tidak dapat diubah.")
        detail = attrs.get("detail")
        if detail is not None and not detail:
            raise serializers.ValidationError("Tagihan harus memiliki minimal satu rincian.")
        return attrs

    def create(self, validated_data):
        detail_data = validated_data.pop("detail")
        total = sum((d["nominal"] for d in detail_data), Decimal(0))
        tagihan = Tagihan.objects.create(**validated_data, total=total, status="BELUM")
        for d in detail_data:
            if not d.get("kategori"):
                d["kategori"] = "BULANAN" if d["komponen"] in ("SPP", "KATERING", "JEMPUTAN") else "LAIN"
            TagihanDetail.objects.create(tagihan=tagihan, **d)
        return tagihan

    def update(self, instance, validated_data):
        detail_data = validated_data.pop("detail", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if detail_data is not None:
            instance.detail.all().delete()
            total = Decimal(0)
            for d in detail_data:
                if not d.get("kategori"):
                    d["kategori"] = "BULANAN" if d["komponen"] in ("SPP", "KATERING", "JEMPUTAN") else "LAIN"
                TagihanDetail.objects.create(tagihan=instance, **d)
                total += d["nominal"]
            instance.total = total
        instance.save()
        return instance
