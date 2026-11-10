"""API Learning Support Unit: paket 8/16 pertemuan dan catatan pertemuan oleh TU."""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import ADMINISTRATION, FINANCE, PRINCIPAL, role_permission
from operations.models import PaketLSU, PertemuanLSU
from operations.services import lsu


class PertemuanLSUSerializer(serializers.ModelSerializer):
    class Meta:
        model = PertemuanLSU
        fields = ["id", "tanggal", "catatan"]


class PaketLSUSerializer(serializers.ModelSerializer):
    siswa_nama = serializers.CharField(source="siswa.nama", read_only=True)
    sesi_terpakai = serializers.SerializerMethodField()
    tagihan_status = serializers.CharField(source="tagihan.status", read_only=True, allow_null=True, default=None)
    tagihan_sisa = serializers.DecimalField(
        source="tagihan.sisa_tagihan", max_digits=18, decimal_places=2, read_only=True, allow_null=True, default=None,
    )
    pertemuan = PertemuanLSUSerializer(many=True, read_only=True)

    class Meta:
        model = PaketLSU
        fields = [
            "id", "siswa", "siswa_nama", "jumlah_sesi", "harga", "tanggal_mulai", "keterangan",
            "sesi_terpakai", "tagihan", "tagihan_status", "tagihan_sisa", "pertemuan",
        ]
        read_only_fields = ["tagihan"]

    def get_sesi_terpakai(self, obj) -> int:
        return len(obj.pertemuan.all())

    def create(self, validated_data):
        request = self.context.get("request")
        try:
            return lsu.buat_paket(user=getattr(request, "user", None), **validated_data)
        except ValueError as exc:
            raise ValidationError(str(exc))


class PertemuanInputSerializer(serializers.Serializer):
    tanggal = serializers.DateField()
    catatan = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class PaketLSUViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Paket tidak diubah setelah dibuat (tagihan sudah terbentuk); hapus lalu buat ulang bila salah."""

    queryset = (
        PaketLSU.objects.select_related("siswa", "tagihan")
        .prefetch_related("pertemuan", "tagihan__pembayaran")
    )
    serializer_class = PaketLSUSerializer
    permission_classes = [role_permission(read=(ADMINISTRATION, FINANCE, PRINCIPAL), write=(ADMINISTRATION,))]
    filterset_fields = ["siswa"]

    def perform_destroy(self, instance):
        try:
            lsu.hapus_paket(instance, user=self.request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))

    @extend_schema(request=PertemuanInputSerializer, responses=PaketLSUSerializer)
    @action(detail=True, methods=["post"])
    def pertemuan(self, request, pk=None):
        """Catat satu pertemuan (rekap dari terapis)."""
        data = PertemuanInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            lsu.catat_pertemuan(self.get_object(), user=request.user, **data.validated_data)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(self.get_queryset().get(pk=pk)).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=PaketLSUSerializer)
    @action(detail=True, methods=["delete"], url_path=r"pertemuan/(?P<pertemuan_id>\d+)")
    def hapus_pertemuan(self, request, pk=None, pertemuan_id=None):
        """Hapus catatan pertemuan yang salah input."""
        deleted, _ = self.get_object().pertemuan.filter(pk=pertemuan_id).delete()
        if not deleted:
            raise ValidationError("Catatan pertemuan tidak ditemukan.")
        return Response(self.get_serializer(self.get_queryset().get(pk=pk)).data)
