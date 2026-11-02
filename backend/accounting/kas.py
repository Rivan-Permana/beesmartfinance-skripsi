"""Akun kas/bank yang boleh menerima atau mengeluarkan uang.

Akun kas lama ditetapkan per kode. Akun kas baru (mis. Kas PG, Kas TK) cukup dibuat Keuangan di
halaman COA dengan kode berawalan 1 dan nama berawalan "Kas ".
"""

from django.db.models import Q

KAS_LEGACY = ("111", "112", "1011", "1101", "1102")


def akun_kas_q():
    return Q(kode_akun__in=KAS_LEGACY) | Q(kode_akun__startswith="1", nama_akun__istartswith="kas ")


def is_akun_kas(kode_akun, nama_akun):
    kode, nama = str(kode_akun), (nama_akun or "").casefold()
    return kode in KAS_LEGACY or (kode.startswith("1") and nama.startswith("kas "))
