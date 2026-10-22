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
    ikut_potongan = serializers.SerializerMethodField()

    def get_ikut_potongan(self, obj) -> bool:
        jurnal = obj.jurnal
        return obj.is_legacy or (jurnal is not None and jurnal.status == "POSTED" and not jurnal.reversals.all())

    class Meta:
        model = PinjamanPegawai
        fields = [
            "id", "pegawai", "tanggal_pinjaman", "jumlah_pinjaman", "tenor_bulan",
            "angsuran_per_bulan", "sudah_terbayar", "sisa_pinjaman", "jurnal", "is_legacy", "ikut_potongan",
        ]
        read_only_fields = ["jurnal", "is_legacy"]


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
    total_biaya = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    total_terbayar = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    sisa_biaya = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    perlu_rekonsiliasi = serializers.BooleanField(read_only=True)
    sitin_terbayar = serializers.SerializerMethodField()
    formulir_terbayar = serializers.SerializerMethodField()
    pembayaran = serializers.SerializerMethodField()

    def get_sitin_terbayar(self, obj) -> bool | None:
        return None if obj.perlu_rekonsiliasi else obj.pembayaran_aktif("SITIN")

    def get_formulir_terbayar(self, obj) -> bool | None:
        return None if obj.perlu_rekonsiliasi else obj.pembayaran_aktif("FORMULIR")

    def get_pembayaran(self, obj) -> list[dict]:
        result = {}
        for komponen, jurnal in [("SITIN", obj.jurnal_sitin), ("FORMULIR", obj.jurnal_pendaftaran)]:
            if not jurnal:
                continue
            key = str(jurnal.pk)
            if key not in result:
                result[key] = {"jurnal_id": key, "tanggal": jurnal.tanggal, "no_bukti": jurnal.no_bukti,
                    "nominal": str(sum((d.debit for d in jurnal.detail.all()), 0)), "status": jurnal.status,
                    "dibatalkan": not obj.pembayaran_aktif(komponen), "komponen": []}
            result[key]["komponen"].append(komponen)
        return list(result.values())

    def validate(self, attrs):
        sitin = attrs.get("biaya_sitin", getattr(self.instance, "biaya_sitin", Decimal(0)))
        formulir = attrs.get("biaya_formulir", getattr(self.instance, "biaya_formulir", None))
        if formulir is not None and sitin + formulir > Decimal("9999999999999999.99"):
            raise serializers.ValidationError("Total biaya melebihi batas nominal yang dapat dicatat.")
        if self.instance:
            for field in ("biaya_sitin", "biaya_formulir"):
                if (self.instance.jurnal_sitin_id or self.instance.jurnal_pendaftaran_id) and field in attrs and attrs[field] != getattr(self.instance, field):
                    raise serializers.ValidationError("Rincian biaya dengan riwayat penerimaan tidak dapat diubah. Cocokkan bukti pembayaran terlebih dahulu.")
            if self.instance.status != "TRIAL" and any(value != getattr(self.instance, field) for field, value in attrs.items()):
                raise serializers.ValidationError("Pendaftaran yang sudah terdaftar atau batal tidak dapat diedit di sini.")
            if self.instance.perlu_rekonsiliasi and "biaya_formulir" in attrs and "biaya_sitin" not in attrs:
                raise serializers.ValidationError("Isi kedua komponen biaya secara eksplisit untuk memetakan data lama.")
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = PendaftaranSiswa.all_objects.select_for_update().get(pk=instance.pk)
        if instance.is_deleted:
            raise serializers.ValidationError("Pendaftaran sudah dihapus.")
        self.instance = instance
        self.validate(validated_data)
        return super().update(instance, validated_data)

    class Meta:
        model = PendaftaranSiswa
        fields = [
            "id", "nama_calon", "jenjang", "tanggal_daftar",
            "biaya_sitin", "biaya_formulir", "biaya_pendaftaran", "status", "siswa",
            "jurnal_sitin", "jurnal_pendaftaran",
            "total_biaya", "total_terbayar", "sisa_biaya", "perlu_rekonsiliasi",
            "sitin_terbayar", "formulir_terbayar", "pembayaran",
        ]
        read_only_fields = ["status", "siswa", "jurnal_sitin", "jurnal_pendaftaran", "biaya_pendaftaran"]
        extra_kwargs = {"biaya_sitin": {"required": True, "min_value": 0},
                        "biaya_formulir": {"required": True, "allow_null": False, "min_value": 0}}


class BayarPendaftaranInputSerializer(serializers.Serializer):
    komponen = serializers.ListField(child=serializers.ChoiceField(choices=["SITIN", "FORMULIR"]), allow_empty=False)
    tanggal = serializers.DateField()
    no_bukti = serializers.CharField(max_length=50)
    nominal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    akun_kas = serializers.CharField(max_length=20)


class FinalisasiPendaftaranInputSerializer(serializers.Serializer):
    spp_nominal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)


class BayarPendaftaranResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)
    jurnal_id = serializers.UUIDField(read_only=True)
    pendaftaran = PendaftaranSiswaSerializer(read_only=True)


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
