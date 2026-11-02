"""API kode pengeluaran sekolah (pemetaan kode singkat -> akun COA)."""

from rest_framework import viewsets

from accounts.permissions import IsFinanceOrReadOnly
from operations.models import KodePengeluaran
from operations.serializers import KodePengeluaranSerializer


class KodePengeluaranViewSet(viewsets.ModelViewSet):
    queryset = KodePengeluaran.objects.select_related("akun")
    serializer_class = KodePengeluaranSerializer
    permission_classes = [IsFinanceOrReadOnly]
    pagination_class = None
