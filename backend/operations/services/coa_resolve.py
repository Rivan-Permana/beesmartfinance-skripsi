"""Resolve kode akun sistem untuk auto-jurnal — selaras COA Final Lebah Madu."""

from __future__ import annotations

from accounting.models import MsCoa, MsSubGolongan

# Urutan kandidat: COA Final dulu, lalu kode legacy seed lama.
SYSTEM_ACCOUNTS: dict[str, dict] = {
    "KAS": {
        "label": "Kas",
        "candidates": ["112", "111", "1101"],
    },
    "BEBAN_GAJI": {
        "label": "Beban Gaji Pegawai",
        "candidates": ["5301", "5201", "5101"],
    },
    "PIUTANG_KARYAWAN": {
        "label": "Piutang Karyawan (kasbon)",
        "ensure_code": "114",
        "ensure_nama": "Piutang Karyawan (Kasbon)",
    },
    "UTANG_ASURANSI": {
        "label": "Utang potongan gaji / BPJS",
        "candidates": ["211", "212", "2101"],
    },
    "LABA_DITAHAN": {
        "label": "Laba Ditahan (tutup buku)",
        "candidates": ["312", "3102"],
    },
}

_LABEL_BY_KEY = {k: v["label"] for k, v in SYSTEM_ACCOUNTS.items()}

# Mapping komponen tagihan/registrasi → kode pendapatan COA Final (fallback legacy di akhir).
TAGIHAN_COMPONENT_ACCOUNTS: dict[str, list[str]] = {
    "SPP": ["411", "4101"],
    "UANG_MASUK": ["412"],
    "PENGEMBANGAN": ["413"],
    "KOMITE": ["414"],
    "KATERING": ["412", "417"],
    "JEMPUTAN": ["417", "412"],
    "KEGIATAN": ["417"],
    "SERAGAM": ["417", "413"],
    "PORTOFOLIO": ["417"],
    "LAIN": ["417", "412"],
}
REGISTRASI_COMPONENT_ACCOUNTS: dict[str, list[str]] = {
    "SITIN": ["416"],
    "PENDAFTARAN": ["415"],
}

_KOMPONEN_EVENT: dict[str, str] = {
    "SITIN": "REGISTRASI",
    "PENDAFTARAN": "REGISTRASI",
}

_KOMPONEN_LABEL: dict[str, str] = {
    "SPP": "SPP",
    "KATERING": "Katering",
    "JEMPUTAN": "Jemputan",
    "UANG_MASUK": "Uang Masuk",
    "KEGIATAN": "Uang Kegiatan",
    "PENGEMBANGAN": "Uang Pengembangan",
    "SERAGAM": "Seragam",
    "KOMITE": "Iuran Komite",
    "PORTOFOLIO": "Portofolio",
    "LAIN": "Komponen Lain",
    "SITIN": "Sit In / Observasi",
    "PENDAFTARAN": "Biaya Pendaftaran",
}


def _pick_active(candidates: list[str]) -> str | None:
    for kode in candidates:
        if MsCoa.objects.filter(kode_akun=kode, is_active=True).exists():
            return kode
    return None


def ensure_piutang_karyawan() -> str:
    """Pastikan akun piutang kasbon ada (114 di bawah aset lancar)."""
    meta = SYSTEM_ACCOUNTS["PIUTANG_KARYAWAN"]
    existing = _pick_active([meta["ensure_code"]])
    if existing:
        return existing

    # Kode legacy 1103 juga dipakai untuk perlengkapan; cek nama sebelum memakainya.
    legacy = MsCoa.objects.filter(
        kode_akun="1103", is_active=True, nama_akun__icontains="piutang",
    ).first()
    if legacy:
        return legacy.kode_akun

    kode = meta["ensure_code"]
    sub = (
        MsSubGolongan.objects.filter(kode_sub="11").first()
        or MsSubGolongan.objects.filter(kode_sub__startswith="1").order_by("kode_sub").first()
    )
    if not sub:
        raise ValueError(
            "Akun piutang karyawan (kasbon) belum ada dan sub-golongan aset lancar tidak ditemukan. "
            "Import COA Final terlebih dahulu."
        )
    MsCoa.objects.get_or_create(
        kode_akun=kode,
        defaults={
            "sub_golongan": sub,
            "nama_akun": meta["ensure_nama"],
            "posisi_normal": "D",
            "is_active": True,
        },
    )
    return kode


def resolve_system_account(key: str, *, legacy_default: str | None = None) -> str:
    """Ambil kode akun aktif untuk komponen sistem (KAS, BEBAN_GAJI, …)."""
    from operations.models import MsPostingRule

    rule = MsPostingRule.objects.filter(komponen=key, aktif=True).first()
    if rule:
        account = MsCoa.objects.filter(kode_akun=rule.akun_kredit_id, is_active=True).first()
        if account and (key != "PIUTANG_KARYAWAN" or "PIUTANG" in account.nama_akun.upper()):
            return account.kode_akun

    meta = SYSTEM_ACCOUNTS.get(key)
    if meta:
        if key == "PIUTANG_KARYAWAN":
            return ensure_piutang_karyawan()
        found = _pick_active(meta["candidates"])
        if found:
            return found

    if legacy_default and MsCoa.objects.filter(kode_akun=legacy_default, is_active=True).exists():
        return legacy_default

    label = _LABEL_BY_KEY.get(key, key)
    raise ValueError(
        f"Akun COA untuk {label} belum dikonfigurasi. "
        "Hubungi Staff Keuangan untuk import bagan akun (COA)."
    )


def validate_jurnal_accounts(kode_list: list[str]) -> None:
    """Validasi semua kode akun ada sebelum insert jurnal."""
    missing = [
        k for k in kode_list
        if not MsCoa.objects.filter(kode_akun=k, is_active=True).exists()
    ]
    if not missing:
        return
    labels = ", ".join(sorted(set(missing)))
    raise ValueError(
        f"Akun COA belum terdaftar: {labels}. "
        "Hubungi Staff Keuangan untuk memeriksa bagan akun."
    )


def resolve_komponen_pendapatan(komponen: str, *, event_code: str | None = None) -> str:
    """Resolve akun pendapatan untuk komponen tagihan/registrasi.

    Urutan: MsPostingRule → mapping COA Final → akun pendapatan umum.
    """
    from operations.models import MsPostingRule

    event = event_code or _KOMPONEN_EVENT.get(komponen, "TAGIHAN")
    rule = MsPostingRule.objects.filter(
        event_code=event, komponen=komponen, aktif=True,
    ).first()
    if rule and MsCoa.objects.filter(kode_akun=rule.akun_kredit_id, is_active=True).exists():
        return rule.akun_kredit_id

    candidates_map = (
        REGISTRASI_COMPONENT_ACCOUNTS if event == "REGISTRASI" else TAGIHAN_COMPONENT_ACCOUNTS
    )
    candidates = candidates_map.get(komponen, candidates_map.get("LAIN", ["411"]))
    found = _pick_active(candidates)
    if found:
        return found

    fallback = _pick_active(["411", "4101"]) or (
        MsCoa.objects.filter(kode_akun__startswith="41", is_active=True)
        .order_by("kode_akun")
        .values_list("kode_akun", flat=True)
        .first()
    )
    if fallback:
        return fallback

    label = _KOMPONEN_LABEL.get(komponen, komponen.replace("_", " ").title())
    raise ValueError(
        f"Akun pendapatan untuk {label} belum dikonfigurasi. "
        "Hubungi Staff Keuangan untuk import bagan akun (COA) dan mapping auto-jurnal."
    )


def seed_system_posting_rules() -> dict[str, str]:
    """Buat/update MsPostingRule untuk akun sistem (tagihan + payroll)."""
    from operations.models import MsPostingRule

    kas_kode = _pick_active(SYSTEM_ACCOUNTS["KAS"]["candidates"])
    if not kas_kode:
        raise ValueError("Akun kas (111/112) belum ada. Import COA Final terlebih dahulu.")

    fallback_pendapatan = _pick_active(["411", "4101"]) or (
        MsCoa.objects.filter(kode_akun__startswith="41", is_active=True)
        .order_by("kode_akun")
        .values_list("kode_akun", flat=True)
        .first()
    )
    beban_kode = _pick_active(SYSTEM_ACCOUNTS["BEBAN_GAJI"]["candidates"])
    if not beban_kode:
        raise ValueError("Akun beban gaji (5301) belum ada. Import COA Final terlebih dahulu.")
    piutang_kode = ensure_piutang_karyawan()
    utang_kode = _pick_active(SYSTEM_ACCOUNTS["UTANG_ASURANSI"]["candidates"])
    if not utang_kode:
        raise ValueError("Akun utang potongan (211) belum ada. Import COA Final terlebih dahulu.")

    mapped = {
        "KAS": kas_kode,
        "BEBAN_GAJI": beban_kode,
        "PIUTANG_KARYAWAN": piutang_kode,
        "UTANG_ASURANSI": utang_kode,
    }

    for komp, kode in mapped.items():
        MsPostingRule.objects.update_or_create(
            event_code="SISTEM",
            komponen=komp,
            defaults={
                "akun_debit_id": kas_kode,
                "akun_kredit_id": kode,
                "aktif": True,
            },
        )

    if fallback_pendapatan:
        tagihan_komponen = [
            "SPP", "KATERING", "JEMPUTAN", "UANG_MASUK", "KEGIATAN",
            "PENGEMBANGAN", "SERAGAM", "KOMITE", "PORTOFOLIO", "LAIN",
        ]
        for komp in tagihan_komponen:
            kredit = _pick_active(TAGIHAN_COMPONENT_ACCOUNTS.get(komp, ["411"])) or fallback_pendapatan
            MsPostingRule.objects.update_or_create(
                event_code="TAGIHAN",
                komponen=komp,
                defaults={
                    "akun_debit_id": kas_kode,
                    "akun_kredit_id": kredit,
                    "aktif": True,
                },
            )
        for komp, candidates in REGISTRASI_COMPONENT_ACCOUNTS.items():
            kredit = _pick_active(candidates) or fallback_pendapatan
            MsPostingRule.objects.update_or_create(
                event_code="REGISTRASI",
                komponen=komp,
                defaults={
                    "akun_debit_id": kas_kode,
                    "akun_kredit_id": kredit,
                    "aktif": True,
                },
            )

    return mapped
