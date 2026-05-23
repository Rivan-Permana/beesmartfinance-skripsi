"""API core accounting: COA (read-only) + Jurnal dgn maker-checker."""

from django.db import DatabaseError, transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsFinance, IsPrincipal

from .models import MsCoa, TrJurnal
from .serializers import MsCoaSerializer, TrJurnalSerializer
from .utils import audit_user


class MsCoaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    queryset = MsCoa.objects.filter(is_active=True).order_by("kode_akun")
    serializer_class = MsCoaSerializer
    permission_classes = [IsAuthenticated]


class TrJurnalViewSet(viewsets.ModelViewSet):
    serializer_class = TrJurnalSerializer

    def get_queryset(self):
        return (
            TrJurnal.objects.filter(is_deleted=False)
            .prefetch_related("detail")
            .order_by("-tanggal", "no_bukti")
        )

    def get_permissions(self):
        # Finance: buat/ubah draft & submit. Principal: approve/post.
        if self.action in ("create", "update", "partial_update", "submit"):
            return [IsFinance()]
        if self.action == "approve":
            return [IsPrincipal()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """DRAFT -> PENDING (maker mengajukan)."""
        jurnal = self.get_object()
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
                jurnal.status = "POSTED"
                jurnal.approved_by = request.user
                jurnal.approved_at = timezone.now()
                jurnal.posted_at = timezone.now()
                jurnal.save(
                    update_fields=["status", "approved_by", "approved_at", "posted_at"]
                )
        except DatabaseError as exc:
            raise ValidationError(str(exc).strip().splitlines()[0])
        return Response(self.get_serializer(jurnal).data, status=status.HTTP_200_OK)
