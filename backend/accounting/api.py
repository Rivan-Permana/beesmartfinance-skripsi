"""API core accounting: COA (read-only) + Jurnal dgn maker-checker."""

from django.db import DatabaseError, transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.response import Response

from accounts.permissions import IsFinance, IsFinanceOrReadOnly, IsPrincipal

from config.db_errors import humanize_db_error

from .models import (
    MsCoa,
    MsGolongan,
    MsPeriodeAkuntansi,
    MsSubGolongan,
    TrAnggaran,
    TrJurnal,
)
from .serializers import (
    MsCoaSerializer,
    MsGolonganSerializer,
    MsPeriodeAkuntansiSerializer,
    MsSubGolonganSerializer,
    TrAnggaranSerializer,
    TrJurnalSerializer,
)
from .services import can_finance_post, close_period, post_jurnal, post_reversal
from .utils import audit_user


class MsGolonganViewSet(viewsets.ModelViewSet):
    queryset = MsGolongan.objects.order_by("kode_golongan")
    serializer_class = MsGolonganSerializer
    permission_classes = [IsFinanceOrReadOnly]


class MsSubGolonganViewSet(viewsets.ModelViewSet):
    queryset = MsSubGolongan.objects.order_by("kode_sub")
    serializer_class = MsSubGolonganSerializer
    permission_classes = [IsFinanceOrReadOnly]


class MsCoaViewSet(viewsets.ModelViewSet):
    queryset = MsCoa.objects.order_by("kode_akun")
    serializer_class = MsCoaSerializer
    permission_classes = [IsFinanceOrReadOnly]

    def perform_create(self, serializer):
        with transaction.atomic(), audit_user(self.request.user):
            serializer.save()

    def perform_update(self, serializer):
        with transaction.atomic(), audit_user(self.request.user):
            serializer.instance = MsCoa.objects.select_for_update().get(pk=serializer.instance.pk)
            serializer.validate(serializer.validated_data)
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic(), audit_user(self.request.user):
            instance = MsCoa.objects.select_for_update().get(pk=instance.pk)
            if instance.saldo_awal:
                raise ValidationError("Akun dengan saldo awal bukan nol tidak dapat dihapus.")
            instance.delete()


class MsPeriodeAkuntansiViewSet(viewsets.ModelViewSet):
    queryset = MsPeriodeAkuntansi.objects.order_by("-tgl_mulai")
    serializer_class = MsPeriodeAkuntansiSerializer
    permission_classes = [IsFinanceOrReadOnly]

    def perform_destroy(self, instance):
        if instance.status == "CLOSED":
            raise ValidationError("Periode yang sudah ditutup tidak dapat dihapus.")
        instance.delete()

    @action(detail=True, methods=["post"], permission_classes=[IsPrincipal])
    def tutup(self, request, pk=None):
        """Tutup buku (fiscal year closing) -> jurnal penutup + status CLOSED."""
        periode = self.get_object()
        try:
            jurnal = close_period(periode, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        periode.refresh_from_db()
        return Response({
            "detail": f"Periode {periode.kode} berhasil ditutup; jurnal penutup dibuat.",
            "periode": self.get_serializer(periode).data,
            "jurnal_penutup": str(jurnal.id),
        })


class TrAnggaranViewSet(viewsets.ModelViewSet):
    queryset = TrAnggaran.objects.order_by("-tahun_anggaran", "kode_akun")
    serializer_class = TrAnggaranSerializer
    permission_classes = [IsFinanceOrReadOnly]


class JurnalPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class BatalPenerimaanInputSerializer(serializers.Serializer):
    alasan = serializers.CharField(max_length=500)


@extend_schema_view(list=extend_schema(parameters=[OpenApiParameter("jenis", str, enum=["masuk", "keluar"])]))
class TrJurnalViewSet(viewsets.ModelViewSet):
    serializer_class = TrJurnalSerializer
    pagination_class = JurnalPagination
    filterset_fields = ["status", "tipe_sumber"]
    search_fields = ["no_bukti", "keterangan"]
    ordering_fields = ["tanggal", "no_bukti"]

    def get_queryset(self):
        queryset = (
            TrJurnal.objects.filter(is_deleted=False)
            .select_related("pembayaran_tagihan__tagihan")
            .prefetch_related("detail", "pendaftaran_sitin", "pendaftaran_admission", "reversals")
            .order_by("-tanggal", "no_bukti")
        )
        jenis = self.request.query_params.get("jenis")
        if jenis:
            if jenis not in ("masuk", "keluar"):
                raise ValidationError("Jenis jurnal harus masuk atau keluar.")
            queryset = queryset.filter(detail__kode_akun__kode_akun__startswith="4" if jenis == "masuk" else "5").distinct()
        return queryset

    def get_permissions(self):
        # Finance: buat/ubah draft, submit, hapus draft. Principal: approve, void.
        if self.action in ("create", "update", "partial_update", "submit", "destroy", "catat", "batal_penerimaan"):
            return [IsFinance()]
        if self.action in ("approve", "void"):
            return [IsPrincipal()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        with transaction.atomic(), audit_user(self.request.user):
            serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        with transaction.atomic(), audit_user(self.request.user):
            instance = TrJurnal.objects.select_for_update().get(pk=instance.pk)
            if instance.status != "DRAFT" or instance.tipe_sumber != "MANUAL":
                raise ValidationError("Hanya jurnal manual DRAFT yang bisa dihapus.")
            instance.detail.all().delete()
            instance.delete()

    def perform_update(self, serializer):
        if serializer.instance.status != "DRAFT":
            raise ValidationError("Hanya jurnal DRAFT yang bisa diubah.")
        with transaction.atomic(), audit_user(self.request.user):
            serializer.save()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """DRAFT -> PENDING (maker mengajukan)."""
        jurnal = self.get_object()
        if can_finance_post(jurnal):
            return self.catat(request, pk)
        if jurnal.status != "DRAFT":
            raise ValidationError("Hanya jurnal DRAFT yang bisa di-submit.")
        jurnal.status = "PENDING"
        jurnal.submitted_by = request.user
        jurnal.save(update_fields=["status", "submitted_by"])
        return Response(self.get_serializer(jurnal).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """PENDING -> POSTED (checker menyetujui). SoD: approver != maker."""
        jurnal = self.get_object()
        if jurnal.status != "PENDING":
            raise ValidationError("Hanya jurnal PENDING yang bisa di-approve.")
        if jurnal.created_by_id == request.user.id:
            raise PermissionDenied("Approver tidak boleh sama dengan pembuat (SoD).")

        # set user utk audit trigger + biarkan trigger DB menegakkan aturan posting
        # (hard-block anggaran, periode CLOSED, dll). Error trigger -> 400.
        try:
            with transaction.atomic(), audit_user(request.user):
                jurnal = post_jurnal(jurnal, request.user, approve=True)
        except ValueError as exc:
            raise ValidationError(str(exc))
        except DatabaseError as exc:
            msg = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
            raise ValidationError(humanize_db_error(msg))
        return Response(self.get_serializer(jurnal).data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def catat(self, request, pk=None):
        """Finance mencatat pemasukan/pengeluaran tanpa approval Kepsek."""
        try:
            jurnal = post_jurnal(self.get_object(), request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(jurnal).data)

    @extend_schema(request=BatalPenerimaanInputSerializer)
    @action(detail=True, methods=["post"], url_path="batal-penerimaan")
    def batal_penerimaan(self, request, pk=None):
        from operations.services.billing import batalkan_pembayaran_draft
        payload = BatalPenerimaanInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            target = self.get_object()
            if target.tipe_sumber in {"AUTO_PENDAFTARAN", "AUTO_SITIN"}:
                from operations.services.registration import batalkan_penerimaan_pendaftaran
                jurnal = batalkan_penerimaan_pendaftaran(target, request.user, payload.validated_data["alasan"])
            else:
                jurnal = batalkan_pembayaran_draft(target, request.user, payload.validated_data["alasan"])
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(jurnal).data)

    @action(detail=True, methods=["post"], permission_classes=[IsPrincipal])
    def void(self, request, pk=None):
        """Batalkan jurnal POSTED via reversing entry (jurnal asli tetap utuh)."""
        jurnal = self.get_object()
        try:
            pembalik = post_reversal(jurnal, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({
            "detail": "Jurnal berhasil dibatalkan via jurnal pembalik.",
            "pembalik": self.get_serializer(pembalik).data,
        }, status=status.HTTP_201_CREATED)
