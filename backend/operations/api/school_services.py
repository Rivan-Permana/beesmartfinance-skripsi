"""API domain layanan sekolah (katering & jemputan)."""

import django_filters
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdministration

from operations.models import ArmadaJemputan, MenuKatering, PendaftaranJemputan
from operations.serializers import (
    ArmadaJemputanSerializer,
    MenuKateringSerializer,
    PendaftaranJemputanSerializer,
)
from operations.services.katering_tarif import (
    get_tarif_katering_harian,
    get_tarif_katering_period,
    set_tarif_katering_harian,
    set_tarif_katering_period,
)


class MenuKateringFilter(django_filters.FilterSet):
    tanggal__gte = django_filters.DateFilter(field_name="tanggal", lookup_expr="gte")
    tanggal__lte = django_filters.DateFilter(field_name="tanggal", lookup_expr="lte")

    class Meta:
        model = MenuKatering
        fields = ["tanggal", "tanggal__gte", "tanggal__lte"]


class MenuKateringViewSet(viewsets.ModelViewSet):
    queryset = MenuKatering.objects.all().order_by("-tanggal")
    serializer_class = MenuKateringSerializer
    permission_classes = [IsAdministration]
    filterset_class = MenuKateringFilter
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]


class ArmadaJemputanViewSet(viewsets.ModelViewSet):
    queryset = ArmadaJemputan.objects.all().order_by("nama_supir")
    serializer_class = ArmadaJemputanSerializer
    permission_classes = [IsAdministration]


class PendaftaranJemputanViewSet(viewsets.ModelViewSet):
    queryset = PendaftaranJemputan.objects.select_related("siswa", "armada").order_by("-id")
    serializer_class = PendaftaranJemputanSerializer
    permission_classes = [IsAdministration]
    filterset_fields = ["siswa", "armada"]


class TarifKateringSerializer(serializers.Serializer):
    periode_bulan = serializers.IntegerField(min_value=1, max_value=12)
    periode_tahun = serializers.IntegerField(min_value=2000, max_value=2100)
    tarif_harian = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)
    tarif_jumat = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=0, required=False,
    )
    is_default = serializers.BooleanField(read_only=True)


@extend_schema(responses=TarifKateringSerializer)
class TarifKateringView(APIView):
    """Tarif katering per hari per bulan — diset Staf TU, dipakai rekap & tagihan."""

    permission_classes = [IsAdministration]

    def get(self, request):
        try:
            bulan = int(request.query_params.get("bulan", 0))
            tahun = int(request.query_params.get("tahun", 0))
        except (TypeError, ValueError):
            raise ValidationError("bulan dan tahun wajib angka.")
        if not bulan or not tahun:
            raise ValidationError("bulan dan tahun wajib diisi.")
        period = get_tarif_katering_period(bulan, tahun)
        return Response({
            "periode_bulan": bulan,
            "periode_tahun": tahun,
            "tarif_harian": str(period.tarif_sen_kam),
            "tarif_jumat": str(period.tarif_jumat),
            "is_default": period.is_default,
        })

    def put(self, request):
        ser = TarifKateringSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        obj = set_tarif_katering_period(
            d["periode_bulan"],
            d["periode_tahun"],
            d["tarif_harian"],
            d.get("tarif_jumat"),
        )
        return Response({
            "periode_bulan": obj.periode_bulan,
            "periode_tahun": obj.periode_tahun,
            "tarif_harian": str(obj.tarif_harian),
            "tarif_jumat": str(obj.tarif_jumat),
            "is_default": False,
        })
