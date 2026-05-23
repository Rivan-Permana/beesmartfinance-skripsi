"""API operasional: Siswa (Administration) + Tagihan dgn aksi pembayaran."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministration

from .models import Siswa, Tagihan
from .serializers import SiswaSerializer, TagihanSerializer
from .services import post_pembayaran_tagihan


class SiswaViewSet(viewsets.ModelViewSet):
    queryset = Siswa.objects.all().order_by("nama")
    serializer_class = SiswaSerializer
    permission_classes = [IsAdministration]


class TagihanViewSet(viewsets.ModelViewSet):
    serializer_class = TagihanSerializer
    permission_classes = [IsAdministration]

    def get_queryset(self):
        return Tagihan.objects.select_related("siswa").prefetch_related("detail")

    @action(detail=True, methods=["post"])
    def bayar(self, request, pk=None):
        """Catat pembayaran -> auto-journal DRAFT (siklus pendapatan)."""
        tagihan = self.get_object()
        try:
            jurnal = post_pembayaran_tagihan(tagihan, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(
            {"tagihan": self.get_serializer(tagihan).data, "jurnal_id": str(jurnal.id)}
        )
