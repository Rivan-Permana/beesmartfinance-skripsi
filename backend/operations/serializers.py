from decimal import Decimal
from django.db import transaction

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
    PembayaranTagihan,
    AlokasiPembayaranTagihan,
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

    def validate(self, attrs):
        keterangan = attrs.get("keterangan", getattr(self.instance, "keterangan", ""))
        gambar = attrs.get("gambar", getattr(self.instance, "gambar", None))
        if not keterangan.strip() and not gambar:
            raise serializers.ValidationError("Isi keterangan atau unggah foto menu terlebih dahulu.")
        return attrs

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
    total_terbayar = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    class Meta:
        model = TagihanDetail
        fields = ["id", "komponen", "kategori", "keterangan", "akun_pendapatan", "nominal", "total_terbayar"]


class AlokasiPembayaranTagihanSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlokasiPembayaranTagihan
        fields = ["detail", "nominal"]


class PembayaranTagihanSerializer(serializers.ModelSerializer):
    alokasi = AlokasiPembayaranTagihanSerializer(many=True, read_only=True)
    jurnal_status = serializers.CharField(source="jurnal.status", read_only=True)

    class Meta:
        model = PembayaranTagihan
        fields = ["id", "tanggal", "no_bukti", "nominal", "akun_kas", "jurnal", "jurnal_status", "created_by", "dibatalkan", "alasan_batal", "dibatalkan_pada", "alokasi"]


class AlokasiPembayaranInputSerializer(serializers.Serializer):
    detail = serializers.IntegerField(min_value=1)
    nominal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))


class BayarTagihanInputSerializer(serializers.Serializer):
    tanggal = serializers.DateField()
    no_bukti = serializers.CharField(max_length=100)
    nominal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    akun_kas = serializers.CharField(max_length=20)
    request_id = serializers.UUIDField()
    alokasi = AlokasiPembayaranInputSerializer(many=True, allow_empty=False)


class TagihanSerializer(serializers.ModelSerializer):
    detail = TagihanDetailSerializer(many=True)
    siswa_nama = serializers.CharField(source="siswa.nama", read_only=True)
    total_terbayar = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    sisa_tagihan = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    pembayaran = PembayaranTagihanSerializer(many=True, read_only=True)

    class Meta:
        model = Tagihan
        fields = [
            "id", "siswa", "siswa_nama", "periode_bulan", "periode_tahun",
            "total", "status", "jurnal", "detail", "total_terbayar", "sisa_tagihan", "perlu_rekonsiliasi", "pembayaran",
        ]
        read_only_fields = ["status", "jurnal", "total", "perlu_rekonsiliasi"]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if instance and (instance.perlu_rekonsiliasi or instance.jurnal_id or instance.pembayaran.exists()):
            raise serializers.ValidationError("Tagihan dengan riwayat pembayaran tidak dapat diubah.")
        detail = attrs.get("detail")
        if detail is not None and not detail:
            raise serializers.ValidationError("Tagihan harus memiliki minimal satu rincian.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detail_data = validated_data.pop("detail")
        total = sum((d["nominal"] for d in detail_data), Decimal(0))
        tagihan = Tagihan.objects.create(**validated_data, total=total, status="BELUM")
        for d in detail_data:
            if not d.get("kategori"):
                d["kategori"] = "BULANAN" if d["komponen"] in ("SPP", "KATERING", "JEMPUTAN") else "LAIN"
            TagihanDetail.objects.create(tagihan=tagihan, **d)
        return tagihan

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Tagihan.objects.select_for_update().get(pk=instance.pk)
        self.instance = instance
        self.validate(validated_data)
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


class BayarTagihanResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    tagihan = TagihanSerializer()
    pembayaran = PembayaranTagihanSerializer()
    jurnal_id = serializers.UUIDField()
