"""API domain aset tetap."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsFinanceOrReadOnly

from operations.models import FixedAsset
from operations.serializers import FixedAssetSerializer
from operations.services import post_penyusutan


class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all().order_by("nama")
    serializer_class = FixedAssetSerializer
    permission_classes = [IsFinanceOrReadOnly]

    @action(detail=True, methods=["post"])
    def susutkan(self, request, pk=None):
        """Penyusutan periodik -> auto-journal (Dr Beban Depr, Cr Akumulasi)."""
        try:
            jurnal = post_penyusutan(self.get_object(), user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({
            "detail": "Penyusutan aset tercatat dan dijurnal sebagai DRAFT.",
            "jurnal_id": str(jurnal.id),
        })
