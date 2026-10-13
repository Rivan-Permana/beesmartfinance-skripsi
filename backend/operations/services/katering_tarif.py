"""Tarif katering per periode — Sen–Kam & Jumat."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from operations.models import KehadiranSiswa, TarifKatering

DEFAULT_TARIF_SEN_KAM = Decimal("20000")
DEFAULT_TARIF_JUMAT = Decimal("10000")
# Alias lama — tarif_harian = Sen–Kam
DEFAULT_TARIF_KATERING_HARIAN = DEFAULT_TARIF_SEN_KAM


@dataclass(frozen=True)
class TarifKateringPeriod:
    tarif_sen_kam: Decimal
    tarif_jumat: Decimal
    is_default: bool


def get_tarif_katering_period(bulan: int, tahun: int) -> TarifKateringPeriod:
    row = TarifKatering.objects.filter(
        periode_bulan=bulan, periode_tahun=tahun,
    ).first()
    if row:
        return TarifKateringPeriod(
            tarif_sen_kam=row.tarif_harian,
            tarif_jumat=row.tarif_jumat,
            is_default=False,
        )
    return TarifKateringPeriod(
        tarif_sen_kam=DEFAULT_TARIF_SEN_KAM,
        tarif_jumat=DEFAULT_TARIF_JUMAT,
        is_default=True,
    )


def get_tarif_katering_harian(bulan: int, tahun: int) -> tuple[Decimal, bool]:
    """Backward-compat: return (tarif_sen_kam, is_default)."""
    period = get_tarif_katering_period(bulan, tahun)
    return period.tarif_sen_kam, period.is_default


def set_tarif_katering_period(
    bulan: int,
    tahun: int,
    tarif_sen_kam: Decimal,
    tarif_jumat: Decimal | None = None,
) -> TarifKatering:
    if tarif_sen_kam < 0:
        raise ValueError("Tarif Sen–Kam tidak boleh negatif.")
    jumat = DEFAULT_TARIF_JUMAT if tarif_jumat is None else tarif_jumat
    if jumat < 0:
        raise ValueError("Tarif Jumat tidak boleh negatif.")
    obj, _ = TarifKatering.objects.update_or_create(
        periode_bulan=bulan,
        periode_tahun=tahun,
        defaults={"tarif_harian": tarif_sen_kam, "tarif_jumat": jumat},
    )
    return obj


def set_tarif_katering_harian(bulan: int, tahun: int, tarif: Decimal) -> TarifKatering:
    """Backward-compat: set Sen–Kam saja, Jumat tetap default tersimpan."""
    existing = TarifKatering.objects.filter(
        periode_bulan=bulan, periode_tahun=tahun,
    ).first()
    jumat = existing.tarif_jumat if existing else DEFAULT_TARIF_JUMAT
    return set_tarif_katering_period(bulan, tahun, tarif, jumat)


def katering_breakdown_from_records(
    records,
    tarif_sen_kam: Decimal,
    tarif_jumat: Decimal,
) -> tuple[Decimal, int, int, int]:
    """Hitung nominal dari queryset/list KehadiranSiswa dengan ikut_katering."""
    hari_sen_kam = 0
    hari_jumat = 0
    total = Decimal(0)
    for rec in records:
        if not rec.ikut_katering:
            continue
        wd = rec.tanggal.weekday()
        if wd <= 3:
            hari_sen_kam += 1
            total += tarif_sen_kam
        elif wd == 4:
            hari_jumat += 1
            total += tarif_jumat
    return total, hari_sen_kam, hari_jumat, hari_sen_kam + hari_jumat


def katering_breakdown_for_siswa(siswa, bulan: int, tahun: int) -> tuple[Decimal, int, int, int, TarifKateringPeriod]:
    period = get_tarif_katering_period(bulan, tahun)
    qs = KehadiranSiswa.objects.filter(
        siswa=siswa,
        tanggal__year=tahun,
        tanggal__month=bulan,
        ikut_katering=True,
    )
    total, h_sen, h_jum, h_all = katering_breakdown_from_records(
        qs, period.tarif_sen_kam, period.tarif_jumat,
    )
    return total, h_sen, h_jum, h_all, period
