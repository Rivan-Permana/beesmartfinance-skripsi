"""API export CSV layout legacy (katering & jemput)."""

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from accounts.permissions import IsAdministration

from operations.services.legacy_export import (
    export_laporan_jemput_legacy,
    export_laporan_katering_legacy,
)


def _parse_periode(request) -> tuple[int, int]:
    try:
        bulan = int(request.query_params.get("bulan", 0))
        tahun = int(request.query_params.get("tahun", 0))
    except (TypeError, ValueError):
        raise ValidationError("bulan dan tahun wajib angka.")
    if not 1 <= bulan <= 12 or not tahun:
        raise ValidationError("bulan (1–12) dan tahun wajib diisi.")
    return bulan, tahun


@extend_schema(responses={(200, "text/csv"): str})
class LegacyExportKateringView(APIView):
    permission_classes = [IsAdministration]

    def get(self, request):
        bulan, tahun = _parse_periode(request)
        body = export_laporan_katering_legacy(bulan, tahun)
        resp = HttpResponse(body, content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = (
            f'attachment; filename="laporan-katering-legacy-{tahun}-{bulan:02d}.csv"'
        )
        return resp


@extend_schema(responses={(200, "text/csv"): str})
class LegacyExportJemputView(APIView):
    permission_classes = [IsAdministration]

    def get(self, request):
        bulan, tahun = _parse_periode(request)
        body = export_laporan_jemput_legacy(bulan, tahun)
        resp = HttpResponse(body, content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = (
            f'attachment; filename="laporan-jemput-legacy-{tahun}-{bulan:02d}.csv"'
        )
        return resp
