"""API domain billing/tagihan (+ generate, bayar, struk)."""

from decimal import Decimal

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministrationWriteFinancePrincipalRead

from operations.models import Siswa, Tagihan
from operations.serializers import TagihanSerializer
from operations.services import (
    generate_batch_tagihan,
    generate_tagihan,
    post_pembayaran_tagihan,
    preview_batch_tagihan,
    preview_tagihan,
    struk_tagihan,
)


class TagihanViewSet(viewsets.ModelViewSet):
    serializer_class = TagihanSerializer
    permission_classes = [IsAdministrationWriteFinancePrincipalRead]
    filterset_fields = ["status", "periode_tahun", "siswa"]

    def get_queryset(self):
        return (
            Tagihan.objects.select_related("siswa")
            .prefetch_related("detail")
            .order_by("-periode_tahun", "-periode_bulan")
        )

    @action(detail=True, methods=["post"])
    def bayar(self, request, pk=None):
        """Catat pembayaran -> auto-journal DRAFT (siklus pendapatan)."""
        tagihan = self.get_object()
        try:
            jurnal = post_pembayaran_tagihan(tagihan, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({
            "detail": "Pembayaran tercatat — jurnal pendapatan DRAFT telah dibuat.",
            "tagihan": self.get_serializer(tagihan).data,
            "jurnal_id": str(jurnal.id),
        })

    @action(detail=False, methods=["post"])
    def preview(self, request):
        """Preview komponen tagihan tanpa menyimpan."""
        try:
            siswa = Siswa.objects.select_related("kelompok__jenjang").get(pk=request.data["siswa"])
            data = preview_tagihan(
                siswa,
                int(request.data["periode_bulan"]),
                int(request.data["periode_tahun"]),
                Decimal(str(request.data.get("tarif_katering", 0))),
            )
        except Siswa.DoesNotExist:
            raise ValidationError("Siswa tidak ditemukan.")
        except (KeyError, ValueError) as exc:
            raise ValidationError({"detail": str(exc)})
        return Response(data)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Rekap otomatis tagihan satu siswa per periode (SPP+katering+jemputan)."""
        try:
            siswa = Siswa.objects.get(pk=request.data["siswa"])
            tagihan = generate_tagihan(
                siswa,
                int(request.data["periode_bulan"]),
                int(request.data["periode_tahun"]),
                Decimal(str(request.data.get("tarif_katering", 0))),
            )
        except Siswa.DoesNotExist:
            raise ValidationError("Siswa tidak ditemukan.")
        except (KeyError, ValueError) as exc:
            raise ValidationError({"detail": str(exc)})
        return Response(self.get_serializer(tagihan).data, status=201)

    @action(detail=False, methods=["post"], url_path="preview-batch")
    def preview_batch(self, request):
        """Preview tagihan batch per jenjang/kelompok."""
        try:
            data = preview_batch_tagihan(
                periode_bulan=int(request.data["periode_bulan"]),
                periode_tahun=int(request.data["periode_tahun"]),
                tarif_katering=Decimal(str(request.data.get("tarif_katering", 0))),
                jenjang_id=request.data.get("jenjang") or None,
                kelompok_id=request.data.get("kelompok") or None,
            )
        except (KeyError, ValueError) as exc:
            raise ValidationError({"detail": str(exc)})
        return Response(data)

    @action(detail=False, methods=["post"], url_path="generate-batch")
    def generate_batch(self, request):
        """Generate tagihan batch per jenjang/kelompok."""
        try:
            data = generate_batch_tagihan(
                periode_bulan=int(request.data["periode_bulan"]),
                periode_tahun=int(request.data["periode_tahun"]),
                tarif_katering=Decimal(str(request.data.get("tarif_katering", 0))),
                jenjang_id=request.data.get("jenjang") or None,
                kelompok_id=request.data.get("kelompok") or None,
            )
        except (KeyError, ValueError) as exc:
            raise ValidationError({"detail": str(exc)})
        return Response(data, status=201)

    @action(detail=True, methods=["get"])
    def struk(self, request, pk=None):
        """Data struk/kwitansi untuk dicetak."""
        return Response(struk_tagihan(self.get_object()))
