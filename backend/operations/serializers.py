from decimal import Decimal
from django.db import transaction

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.permissions import ADMINISTRATION, FINANCE, PRINCIPAL, _in_groups

from .models import (
    AbsenPegawai,
    ArmadaJemputan,
    FixedAsset,
    GajiPegawai,
    Jenjang,
    KehadiranSiswa,
    Kegiatan,
    Kelompok,
    KodePengeluaran,
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
            "status", "status_aktif", "tanggal_mulai_kerja", "tanggal_selesai_kerja", "user",
        ]
        read_only_fields = ["status_aktif"]


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
    jurnal_status = serializers.CharField(source="jurnal.status", read_only=True, allow_null=True, default=None)

    class Meta:
        model = GajiPegawai
        fields = [
            "id", "pegawai", "periode_bulan", "periode_tahun",
            "gaji_pokok", "tunjangan_jabatan", "tunjangan_pengabdian",
            "tunjangan_asuransi", "uang_makan", "transport",
            "bonus_insentif", "thr", "hari_hadir",
            "potongan_pinjaman", "potongan_asuransi",
            "total_bruto", "total_potongan", "total_netto", "jurnal", "jurnal_status",
        ]
        read_only_fields = ["jurnal"]


class GajiPeriodeInputSerializer(serializers.Serializer):
    periode_bulan = serializers.IntegerField(min_value=1, max_value=12)
    periode_tahun = serializers.IntegerField(min_value=2020, max_value=2100)
    simpan = serializers.BooleanField(default=False)


class GajiPeriodeBarisSerializer(serializers.Serializer):
    gaji = serializers.IntegerField()
    pegawai = serializers.IntegerField()
    nama = serializers.CharField()
    netto = serializers.DecimalField(max_digits=18, decimal_places=2)
    status = serializers.ChoiceField(choices=["siap", "berhasil", "gagal"])
    pesan = serializers.CharField(allow_null=True)


class GajiPeriodeHasilSerializer(serializers.Serializer):
    disimpan = serializers.BooleanField()
    jumlah = serializers.IntegerField()
    berhasil = serializers.IntegerField()
    gagal = serializers.IntegerField()
    total_netto = serializers.DecimalField(max_digits=18, decimal_places=2)
    hasil = GajiPeriodeBarisSerializer(many=True)


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
    penanggung_jawab_nama = serializers.CharField(source="penanggung_jawab.nama", read_only=True, default=None)

    class Meta:
        model = Kegiatan
        fields = [
            "id", "nama", "akun_beban", "pagu", "penanggung_jawab", "penanggung_jawab_nama",
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


class BiayaMasukDefaultSerializer(serializers.Serializer):
    uang_masuk = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    uang_pengembangan = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    uang_kegiatan = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    uang_seragam = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)


class BiayaMasukRingkasSerializer(serializers.Serializer):
    tagihan = serializers.IntegerField()
    status = serializers.CharField()
    total = serializers.DecimalField(max_digits=18, decimal_places=2)
    sisa = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)


class ImporBiodataInputSerializer(serializers.Serializer):
    berkas = serializers.FileField()
    kelas_map = serializers.JSONField(binary=True, required=False, help_text="{nilai Kelas di CSV: id kelompok atau null}")
    simpan = serializers.BooleanField(default=False)


class ImporBiodataKelasSerializer(serializers.Serializer):
    kelas = serializers.CharField()
    jumlah = serializers.IntegerField()
    kelompok = serializers.IntegerField(allow_null=True)


class ImporBiodataBarisSerializer(serializers.Serializer):
    baris = serializers.IntegerField()
    kelas = serializers.CharField()
    nama = serializers.CharField()
    aksi = serializers.ChoiceField(choices=["baru", "ubah", "sama", "galat"])
    siswa = serializers.IntegerField(allow_null=True)
    peringatan = serializers.ListField(child=serializers.CharField())
    galat = serializers.CharField(allow_null=True)
    perubahan = serializers.DictField(child=serializers.ListField(allow_null=True))
    nilai = serializers.DictField()


class ImporBiodataRingkasanSerializer(serializers.Serializer):
    baru = serializers.IntegerField()
    ubah = serializers.IntegerField()
    sama = serializers.IntegerField()
    galat = serializers.IntegerField()
    peringatan = serializers.IntegerField()


class ImporBiodataHasilSerializer(serializers.Serializer):
    disimpan = serializers.BooleanField()
    ringkasan = ImporBiodataRingkasanSerializer()
    kelas = ImporBiodataKelasSerializer(many=True)
    baris = ImporBiodataBarisSerializer(many=True)


class ImporSppInputSerializer(serializers.Serializer):
    berkas = serializers.FileField()
    simpan = serializers.BooleanField(default=False)


class ImporSppBarisSerializer(serializers.Serializer):
    baris = serializers.IntegerField()
    nama = serializers.CharField()
    kelas = serializers.CharField(allow_blank=True)
    aksi = serializers.ChoiceField(choices=["isi", "sama", "beda", "cek", "galat"])
    siswa = serializers.IntegerField(allow_null=True)
    spp_lama = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    spp_baru = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    nilai = serializers.ListField(child=serializers.IntegerField())
    alasan = serializers.CharField(allow_null=True)


class ImporSppRingkasanSerializer(serializers.Serializer):
    isi = serializers.IntegerField()
    sama = serializers.IntegerField()
    beda = serializers.IntegerField()
    cek = serializers.IntegerField()
    galat = serializers.IntegerField()


class ImporSppHasilSerializer(serializers.Serializer):
    disimpan = serializers.BooleanField()
    diisi = serializers.IntegerField()
    ringkasan = ImporSppRingkasanSerializer()
    baris = ImporSppBarisSerializer(many=True)


class ImporBiayaMasukInputSerializer(serializers.Serializer):
    berkas = serializers.FileField()
    tanggal = serializers.DateField(help_text="Tanggal saldo awal, mis. 31/12 sebelum cut-over.")
    simpan = serializers.BooleanField(default=False)


class ImporBiayaMasukKomponenSerializer(serializers.Serializer):
    uang_masuk = serializers.IntegerField(allow_null=True)
    uang_portofolio = serializers.IntegerField(allow_null=True)
    uang_kegiatan = serializers.IntegerField(allow_null=True)
    uang_pengembangan = serializers.IntegerField(allow_null=True)
    uang_komite = serializers.IntegerField(allow_null=True)
    uang_seragam = serializers.IntegerField(allow_null=True)


class ImporBiayaMasukBarisSerializer(serializers.Serializer):
    baris = serializers.IntegerField()
    nama = serializers.CharField()
    kelas = serializers.CharField(allow_blank=True)
    aksi = serializers.ChoiceField(choices=["isi", "sudah", "lewati", "cek", "galat"])
    siswa = serializers.IntegerField(allow_null=True)
    kategori = serializers.CharField(allow_blank=True)
    diskon = serializers.IntegerField()
    komponen = ImporBiayaMasukKomponenSerializer()
    ditagih = serializers.IntegerField()
    terbayar = serializers.IntegerField()
    alasan = serializers.CharField(allow_null=True)


class ImporBiayaMasukRingkasanSerializer(serializers.Serializer):
    isi = serializers.IntegerField()
    sudah = serializers.IntegerField()
    lewati = serializers.IntegerField()
    cek = serializers.IntegerField()
    galat = serializers.IntegerField()
    total_ditagih = serializers.IntegerField()
    total_terbayar = serializers.IntegerField()


class ImporBiayaMasukHasilSerializer(serializers.Serializer):
    disimpan = serializers.BooleanField()
    diisi = serializers.IntegerField()
    ringkasan = ImporBiayaMasukRingkasanSerializer()
    baris = ImporBiayaMasukBarisSerializer(many=True)


class SiswaSerializer(serializers.ModelSerializer):
    diskon_kategori = serializers.ListField(
        child=serializers.ChoiceField(choices=Siswa.DISKON_KATEGORI), required=False, allow_empty=True,
    )
    diskon_nominal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal(0), required=False)
    uang_masuk = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    uang_kegiatan = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    uang_pengembangan = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    uang_seragam = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    uang_komite = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    uang_portofolio = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    biaya_masuk = serializers.SerializerMethodField()

    class Meta:
        model = Siswa
        fields = [
            "id", "nis", "nama", "nama_panggilan", "jenis_kelamin", "kelompok",
            "tempat_lahir", "tanggal_lahir", "alamat",
            "nama_ayah", "kontak_ayah", "nama_ibu", "kontak_ibu",
            "spp_nominal", "status", "periode",
            "diskon_kategori", "diskon_nominal",
            "uang_masuk", "uang_kegiatan", "uang_pengembangan", "uang_seragam", "uang_komite", "uang_portofolio",
            "biaya_masuk",
            "ukuran_seragam_putih", "ukuran_seragam_olga",
        ]

    # Guru membaca daftar siswa untuk absensi; nominal biaya hanya untuk TU, Keuangan, Kepsek.
    NOMINAL_FIELDS = (
        "spp_nominal", "diskon_kategori", "diskon_nominal",
        "uang_masuk", "uang_kegiatan", "uang_pengembangan", "uang_seragam", "uang_komite", "uang_portofolio",
        "biaya_masuk",
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request is not None and not _in_groups(request.user, (ADMINISTRATION, FINANCE, PRINCIPAL)):
            for field in self.NOMINAL_FIELDS:
                data.pop(field, None)
        return data

    def validate_diskon_kategori(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Kategori diskon tidak boleh berulang.")
        return [kode for kode, _label in Siswa.DISKON_KATEGORI if kode in value]

    @extend_schema_field(BiayaMasukRingkasSerializer(allow_null=True))
    def get_biaya_masuk(self, obj):
        tagihan = getattr(obj, "tagihan_biaya_masuk", None)
        if tagihan is None:
            tagihan = list(Tagihan.objects.filter(siswa=obj, jenis="BIAYA_MASUK").order_by("-pk")[:1])
        if not tagihan:
            return None
        t = tagihan[0]
        return BiayaMasukRingkasSerializer({"tagihan": t.pk, "status": t.status, "total": t.total, "sisa": t.sisa_tagihan}).data

    def _simpan(self, save, diskon_berubah=False):
        from operations.services.biaya_masuk import sinkron_tagihan_biaya_masuk

        request = self.context.get("request")
        try:
            with transaction.atomic():
                siswa = save()
                sinkron_tagihan_biaya_masuk(siswa, user=getattr(request, "user", None), diskon_berubah=diskon_berubah)
        except ValueError as exc:
            raise serializers.ValidationError({"biaya_masuk": str(exc)})
        siswa.__dict__.pop("tagihan_biaya_masuk", None)
        return siswa

    def create(self, validated_data):
        return self._simpan(lambda: super(SiswaSerializer, self).create(validated_data))

    def update(self, instance, validated_data):
        diskon_berubah = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in ("diskon_nominal", "diskon_kategori")
        )
        return self._simpan(lambda: super(SiswaSerializer, self).update(instance, validated_data), diskon_berubah)


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
    jurnal_status = serializers.CharField(source="jurnal.status", read_only=True, allow_null=True, default=None)

    class Meta:
        model = PembayaranTagihan
        fields = [
            "id", "tanggal", "no_bukti", "nominal", "akun_kas", "jurnal", "jurnal_status", "saldo_awal",
            "created_by", "dibatalkan", "alasan_batal", "dibatalkan_pada", "alokasi",
        ]


class AlokasiPembayaranInputSerializer(serializers.Serializer):
    detail = serializers.IntegerField(min_value=1)
    nominal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))


class BatalSaldoAwalInputSerializer(serializers.Serializer):
    pembayaran = serializers.IntegerField(min_value=1)
    alasan = serializers.CharField(max_length=500)


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
            "id", "siswa", "siswa_nama", "periode_bulan", "periode_tahun", "jenis",
            "total", "status", "jurnal", "detail", "total_terbayar", "sisa_tagihan", "perlu_rekonsiliasi", "pembayaran",
        ]
        read_only_fields = ["status", "jurnal", "total", "perlu_rekonsiliasi", "jenis"]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if instance and (instance.perlu_rekonsiliasi or instance.jurnal_id or instance.pembayaran.exists()):
            raise serializers.ValidationError("Tagihan dengan riwayat pembayaran tidak dapat diubah.")
        if instance and instance.jenis == "BIAYA_MASUK":
            raise serializers.ValidationError("Ubah biaya masuk lewat Data Siswa.")
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


class KelengkapanMasalahSerializer(serializers.Serializer):
    kode = serializers.ChoiceField(choices=["spp_kosong", "spp_janggal", "tanpa_kelompok", "kontak_kosong", "hp_janggal"])
    pesan = serializers.CharField()


class KelengkapanBarisSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nama = serializers.CharField()
    nis = serializers.CharField(allow_null=True)
    kelompok = serializers.CharField(allow_null=True)
    spp_nominal = serializers.DecimalField(max_digits=18, decimal_places=2)
    spp_acuan = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    masalah = KelengkapanMasalahSerializer(many=True)


class KelengkapanRingkasanSerializer(serializers.Serializer):
    spp_kosong = serializers.IntegerField()
    spp_janggal = serializers.IntegerField()
    tanpa_kelompok = serializers.IntegerField()
    kontak_kosong = serializers.IntegerField()
    hp_janggal = serializers.IntegerField()


class KelengkapanHasilSerializer(serializers.Serializer):
    total_siswa = serializers.IntegerField()
    ringkasan = KelengkapanRingkasanSerializer()
    baris = KelengkapanBarisSerializer(many=True)


class InvoiceGabunganLineSerializer(serializers.Serializer):
    tagihan_id = serializers.IntegerField()
    periode = serializers.CharField()
    komponen = serializers.CharField()
    label = serializers.CharField()
    nominal = serializers.DecimalField(max_digits=18, decimal_places=2)


class InvoiceGabunganSectionSerializer(serializers.Serializer):
    kategori = serializers.ChoiceField(choices=["TAHUNAN", "BULANAN", "LAIN"])
    label = serializers.CharField()
    lines = InvoiceGabunganLineSerializer(many=True)


class InvoiceGabunganDicocokkanSerializer(serializers.Serializer):
    tagihan_id = serializers.IntegerField()
    periode = serializers.CharField()
    jenis = serializers.CharField()
    total = serializers.DecimalField(max_digits=18, decimal_places=2)


class InvoiceRekeningSerializer(serializers.Serializer):
    bank = serializers.CharField(allow_blank=True)
    nomor = serializers.CharField()
    atas_nama = serializers.CharField(allow_blank=True)


class InvoiceKontakSerializer(serializers.Serializer):
    nama = serializers.CharField(allow_blank=True)
    wa = serializers.CharField(allow_blank=True)


class InvoiceKontakOrtuSerializer(serializers.Serializer):
    label = serializers.CharField()
    nomor = serializers.CharField()


class InvoiceGabunganSerializer(serializers.Serializer):
    sekolah = serializers.CharField()
    tanggal = serializers.DateField()
    siswa_id = serializers.IntegerField()
    siswa = serializers.CharField()
    nis = serializers.CharField(allow_null=True)
    kelompok = serializers.CharField(allow_null=True)
    jenjang = serializers.CharField(allow_null=True)
    sections = InvoiceGabunganSectionSerializer(many=True)
    total = serializers.DecimalField(max_digits=18, decimal_places=2)
    perlu_dicocokkan = InvoiceGabunganDicocokkanSerializer(many=True)
    rekening = InvoiceRekeningSerializer(allow_null=True)
    kontak = InvoiceKontakSerializer(allow_null=True)
    catatan = serializers.CharField(allow_blank=True)
    kontak_ortu = InvoiceKontakOrtuSerializer(many=True)


class KodePengeluaranSerializer(serializers.ModelSerializer):
    akun_nama = serializers.CharField(source="akun.nama_akun", read_only=True, allow_null=True, default=None)

    class Meta:
        model = KodePengeluaran
        fields = ["id", "kode", "unit", "nama", "akun", "akun_nama", "aktif"]
        validators = []  # keunikan kode+unit dicek di validate() dengan pesan berbahasa Indonesia

    def validate_kode(self, value):
        kode = value.strip().upper()
        if not kode or " " in kode:
            raise serializers.ValidationError("Kode berisi satu kata tanpa spasi, misalnya ATK.")
        return kode

    def validate_akun(self, value):
        if value is not None and not value.is_active:
            raise serializers.ValidationError("Pilih akun yang masih aktif.")
        return value

    def validate(self, attrs):
        kode = attrs.get("kode", getattr(self.instance, "kode", None))
        unit = attrs.get("unit", getattr(self.instance, "unit", "UMUM"))
        sama = KodePengeluaran.objects.filter(kode=kode, unit=unit)
        if self.instance:
            sama = sama.exclude(pk=self.instance.pk)
        if sama.exists():
            raise serializers.ValidationError({"kode": f"Kode {kode} untuk unit ini sudah ada."})
        return attrs
