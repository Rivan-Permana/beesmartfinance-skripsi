#!/usr/bin/env python3
"""Generate logbook bimbingan skripsi BeeSmart Finance from official template (docx + pdf)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "external-docs"
TEMPLATE = OUT_DIR / "LOGBOOK BIMBINGAN SKRIPSI (2).docx"
OUT_DOCX = OUT_DIR / "LOGBOOK BIMBINGAN SKRIPSI - Rivan Permana.docx"
OUT_PDF = OUT_DIR / "LOGBOOK BIMBINGAN SKRIPSI - Rivan Permana.pdf"

JUDUL = (
    "RANCANG BANGUN SISTEM INFORMASI AKUNTANSI PENGELOLAAN KEUANGAN "
    "BERBASIS WEB DENGAN VISUALISASI DASBOR ANALITIK"
)
SUB_JUDUL = "(STUDI KASUS: SEKOLAH LEBAH MADU)"
NAMA = "Rivan Anjung Sinar Permana"
NIM = "2207412050"
PRODI = "Teknik Informatika"
TA = "2025/2026"
PEMBIMBING = "Ariawan Andi Suhandana, S.Kom., M.T.I."

TUJUAN = [
    "Merancang dan mengimplementasikan Sistem Informasi Akuntansi (SIA) berbasis web "
    "untuk pengelolaan keuangan TK/PG Sekolah Lebah Madu dengan prinsip double-entry "
    "accounting dan pemisahan tugas (segregation of duties) antar peran pengguna.",
    "Mengintegrasikan modul operasional sekolah (absensi siswa, katering, jemputan, "
    "tagihan, pegawai, dan kegiatan) dengan modul akuntansi (jurnal, COA, anggaran, "
    "dan laporan keuangan) melalui mekanisme auto-posting di backend.",
    "Menyediakan dasbor analitik dan laporan keuangan yang dapat dimanfaatkan "
    "Kepala Sekolah untuk monitoring dan persetujuan transaksi (maker-checker).",
    "Mengevaluasi sistem menggunakan User Acceptance Testing (UAT) dengan skenario "
    "tiga persona (Admin TU, Staf Keuangan, Kepala Sekolah) di lingkungan sekolah mitra.",
]

MANFAAT = [
    "Memberikan solusi terintegrasi pengganti pencatatan manual/Excel pada operasional "
    "keuangan TK Lebah Madu sehingga alur tagihan hingga jurnal lebih terstruktur dan "
    "teraudit.",
    "Menjadi referensi implementasi SIA sekolah swasta skala kecil dengan RBAC dan "
    "governance akuntansi yang sesuai praktik ISAK 35 / standar akuntansi entitas "
    "nirlaba pendidikan.",
    "Menyediakan dokumentasi dan prototype open-source yang dapat dikembangkan lebih "
    "lanjut (portal orang tua, integrasi pembayaran digital) sebagai lanjutan penelitian.",
]

SESSIONS = [
    {
        "no": 1,
        "tanggal": "Sabtu, 5 April 2026",
        "tempat": "Online / Daring (Google Meet)",
        "uraian": (
            "Bimbingan pertama membahas kesepakatan judul, ruang lingkup penelitian, dan "
            "objek studi kasus TK Lebah Madu. Dosen pembimbing mengarahkan agar fokus pada "
            "SIA operasional sekolah (bukan portal orang tua) dengan tiga kelompok pengguna "
            "utama: Administrasi/TU, Keuangan, dan Kepala Sekolah. Disepakati penyusunan "
            "Bab I–III proposal terlebih dahulu serta persiapan surat izin penelitian ke sekolah."
        ),
        "rencana": (
            "Menyusun draft Bab I–III, mengumpulkan data biaya layanan sekolah (SPP, katering, "
            "jemputan) dari website sekolah, dan mengajukan surat keterangan aktif serta "
            "surat izin penelitian."
        ),
    },
    {
        "no": 2,
        "tanggal": "Senin, 14 April 2026",
        "tempat": "Online / Daring — pukul 13.30 WIB",
        "uraian": (
            "Pembahasan landasan teori SIA, prinsip akuntansi double-entry, dan relevansi "
            "ISAK 35 untuk entitas pendidikan. Dosen memberikan masukan agar Bab II memuat "
            "perbandingan sistem sejenis (SAKOLA, Siswamedia) dan menjelaskan gap sistem "
            "existing yang masih setengah matang (backend kuat, frontend belum lengkap)."
        ),
        "rencana": (
            "Melengkapi tinjauan pustaka dan diagram arsitektur sistem (PostgreSQL + Django "
            "REST + Vue 3). Memulai dokumentasi kebutuhan fungsional per role."
        ),
    },
    {
        "no": 3,
        "tanggal": "Jumat, 25 April 2026",
        "tempat": "Online / Daring",
        "uraian": (
            "Review progress implementasi backend: model ORM, trigger audit log PostgreSQL, "
            "auto-posting tagihan/gaji/aset, dan workflow jurnal (DRAFT → PENDING → POSTED). "
            "Pembimbing menekankan pentingnya segregation of duties dan audit trail untuk "
            "skripsi bidang keamanan/integritas data akuntansi."
        ),
        "rencana": (
            "Menyelesaikan API backend yang belum terdokumentasi, menyiapkan seed data demo "
            "4 role, dan merancang skenario UAT awal."
        ),
    },
    {
        "no": 4,
        "tanggal": "Kamis, 8 Mei 2026",
        "tempat": "Online / Daring — pukul 14.00 WIB",
        "uraian": (
            "Pembahasan metodologi penelitian: SDLC iteratif untuk pengembangan sistem dan "
            "User Acceptance Testing (UAT) di lokasi sekolah. Dibahas juga administrasi "
            "proposal; mahasiswa sempat terkendala surat keterangan mahasiswa aktif sehingga "
            "pengajuan proposal melewati batas waktu dan akan dinegosiasikan perpanjangan."
        ),
        "rencana": (
            "Menyelesaikan kelengkapan administrasi proposal, melanjutkan Bab III metode "
            "penelitian, dan menghubungi pihak sekolah untuk jadwal observasi/UAT."
        ),
    },
    {
        "no": 5,
        "tanggal": "Senin, 19 Mei 2026",
        "tempat": "Online / Daring — pukul 16.30 WIB",
        "uraian": (
            "Bimbingan ditunda dari sore karena jadwal rapat dosen; dilaksanakan sekitar "
            "pukul 16.30. Dibahas desain RBAC empat role (Administration, Finance, "
            "SchoolPrincipal, TeacherInCharge) dan prinsip UI task-based untuk staf non-akuntan. "
            "Pembimbing setuju fitur AI dipangkas agar fokus penelitian pada SIA inti."
        ),
        "rencana": (
            "Memulai pengembangan frontend Vue 3 + PrimeVue sesuai mockup sempro, "
            "menerapkan design system Lebah Madu, dan menyiapkan navigasi per role."
        ),
    },
    {
        "no": 6,
        "tanggal": "Rabu, 28 Mei 2026",
        "tempat": "Online / Daring — pukul 10.30 WIB",
        "uraian": (
            "Review progress frontend: modul siswa, absensi, katering (tarif Rp 22.000/hari), "
            "jemputan, tagihan dengan preview editor, dan shell aplikasi responsif. Dosen "
            "menyarankan kolaborasi dengan Dosen Mata Kuliah Akuntansi (Ibu Vidya) untuk "
            "validasi domain akuntansi sekolah dan rencana UAT di TK Lebah Madu."
        ),
        "rencana": (
            "Menyelesaikan modul keuangan (COA, jurnal, laporan, audit log), integrasi "
            "maker-checker approve jurnal Kepala Sekolah, dan koordinasi UAT dengan pihak sekolah."
        ),
    },
    {
        "no": 7,
        "tanggal": "Kamis, 5 Juni 2026",
        "tempat": "Online / Daring",
        "uraian": (
            "Demonstrasi prototype BeeSmart Finance: alur UJ-1 (Admin TU — absensi → tagihan → "
            "struk), UJ-2 (Keuangan — jurnal & laporan), UJ-3 (Kepsek — approve & dashboard). "
            "Pembimbing mengarahkan penulisan Bab IV (implementasi) dan Bab V (pengujian UAT) "
            "serta persiapan instrumen UAT walkthrough otomatis."
        ),
        "rencana": (
            "Menyelesaikan skrip UAT (uat_walkthrough 31 skenario), Docker/CI, dan draft "
            "Bab IV–V. Melakukan UAT lapangan di sekolah dengan 3 akun role berbeda."
        ),
    },
    {
        "no": 8,
        "tanggal": "Senin, 23 Juni 2026",
        "tempat": "Online / Daring — pukul 13.00 WIB",
        "uraian": (
            "Bimbingan dadakan menjelang uji kompetensi. Dibahas kelengkapan logbook, upload "
            "dokumen ke Google Drive, dan persiapan tanda tangan surat persetujuan skripsi. "
            "Mahasiswa melaporkan UAT otomatis 31/31 lulus; sisa UAT manual di sekolah bersama "
            "Ibu Vidya dan penyusunan kuesioner SUS (System Usability Scale) pasca-UAT."
        ),
        "rencana": (
            "Melakukan UAT di TK Lebah Madu, mendokumentasikan hasil SUS, melengkapi Bab V, "
            "dan menyiapkan pendaftaran sidang akhir."
        ),
    },
    {
        "no": 9,
        "tanggal": "Sabtu, 28 Juni 2026",
        "tempat": "Online / Daring (WhatsApp & telepon)",
        "uraian": (
            "Koordinasi via japri terkait pendaftaran sidang akhir hari Selasa. Pembimbing "
            "menegaskan sistem sudah layak dengan catatan: (1) melengkapi Bab IV–V proposal/laporan, "
            "(2) wajib ada bukti UAT di sekolah, (3) menyiapkan dokumen SUS. Mahasiswa "
            "menyampaikan rencana UAT diwakilkan langsung ke Ibu Vidya dengan 3 role berbeda."
        ),
        "rencana": (
            "Finalisasi laporan skripsi, unggah logbook & laporan terbaru ke Drive, "
            "dan menemui pembimbing untuk penandatanganan form sidang."
        ),
    },
    {
        "no": 10,
        "tanggal": "Minggu, 29 Juni 2026",
        "tempat": "Offline — Halte Tanjung Barat (seberang Cafe Qisas), ± pukul 17.00 WIB",
        "uraian": (
            "Pertemuan offline untuk penandatanganan formulir pendaftaran sidang akhir skripsi. "
            "Pembimbing mengingatkan agar laporan skripsi dan logbook versi terbaru sudah di-upload "
            "ke Google Drive. Disepakati UAT di sekolah tetap wajib dengan dokumentasi SUS; "
            "mahasiswa akan koordinasi lokasi uji dengan Ibu Vidya (Dosen Akuntansi kolaborator). "
            "Status penelitian: backend selesai, frontend ~95%, tinggal UAT lapangan dan "
            "penyempurnaan Bab IV–V."
        ),
        "rencana": (
            "Melaksanakan UAT di TK Lebah Madu, mengumpulkan data SUS, submit pendaftaran sidang "
            "Selasa, dan revisi final laporan skripsi sesuai masukan penguji nanti."
        ),
    },
]


def _qn(tag: str) -> str:
    from docx.oxml.ns import qn

    return qn(tag)


def _copy_ppr(proto_p, *, keep_numbering: bool = False):
    if proto_p is None:
        return None
    p_pr = proto_p.find(W + "pPr")
    if p_pr is None:
        p_pr = proto_p.find(_qn("w:pPr"))
    if p_pr is None:
        return None
    copied = deepcopy(p_pr)
    if not keep_numbering:
        num_pr = copied.find(W + "numPr")
        if num_pr is None:
            num_pr = copied.find(_qn("w:numPr"))
        if num_pr is not None:
            copied.remove(num_pr)
    return copied


def _make_paragraph(text: str | None = None, p_pr_copy=None):
    """Build a clean w:p using raw lxml (avoids python-docx text triplication bug)."""
    p = etree.Element(W + "p")
    if p_pr_copy is not None:
        p.append(p_pr_copy)
    if text:
        r = etree.SubElement(p, W + "r")
        t = etree.SubElement(r, W + "t")
        if text.startswith(" ") or text.endswith(" ") or "\t" in text or "\n" in text:
            t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = text
    return p


def _make_page_break_paragraph():
    p = etree.Element(W + "p")
    r = etree.SubElement(p, W + "r")
    br = etree.SubElement(r, W + "br")
    br.set(f"{{{W_NS}}}type", "page")
    return p


def _make_signature_spacer(line_twips: int = 1200):
    """Empty paragraph with fixed height for signature space (~0.8 inch default)."""
    p = etree.Element(W + "p")
    p_pr = etree.SubElement(p, W + "pPr")
    spacing = etree.SubElement(p_pr, W + "spacing")
    spacing.set(f"{{{W_NS}}}line", str(line_twips))
    spacing.set(f"{{{W_NS}}}lineRule", "exact")
    return p


def _first_paragraph_in_tc(tc):
    for child in tc:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            return child
    return None


def _clear_tc(tc) -> None:
    tc.text = None
    tc.tail = None
    for child in list(tc):
        if child.tag in (W + "p", _qn("w:p")):
            tc.remove(child)


def _set_cell_plain_text(cell, text: str) -> None:
    tc = cell._tc
    template_p = _first_paragraph_in_tc(tc)
    p_pr = _copy_ppr(template_p, keep_numbering=False)
    _clear_tc(tc)
    tc.append(_make_paragraph(text, p_pr))


def _set_cell_numbered_list(cell, items: list[str]) -> None:
    """Word auto-numbering via numPr — jangan tambah '1.' manual di teks."""
    tc = cell._tc
    template_p = _first_paragraph_in_tc(tc)
    p_pr = _copy_ppr(template_p, keep_numbering=True)
    _clear_tc(tc)
    for item in items:
        tc.append(_make_paragraph(item, deepcopy(p_pr) if p_pr is not None else None))


def _clone_paragraph(proto_p, text: str, *, keep_numbering: bool = False):
    return _make_paragraph(text, _copy_ppr(proto_p, keep_numbering=keep_numbering))


def _clone_empty_paragraph(proto_p):
    return _make_paragraph(None, _copy_ppr(proto_p, keep_numbering=False))


def _find_logbook_start_index(body) -> int:
    for idx, child in enumerate(body):
        if child.tag.endswith("}p"):
            text = "".join(child.itertext())
            if "Logbook/Catatan Bimbingan" in text:
                return idx
    raise ValueError("Logbook section not found in template")


def _remove_body_children(body, start: int, end: int) -> None:
    for idx in range(end - 1, start - 1, -1):
        body.remove(body[idx])


def _insert_before_sectpr(body, insert_at: int, elements: list) -> int:
    """Insert elements in forward order before sectPr; return next insert index."""
    for offset, elem in enumerate(elements):
        body.insert(insert_at + offset, elem)
    return insert_at + len(elements)


def _fill_logbook_table(table, session: dict) -> None:
    _set_cell_plain_text(table.rows[0].cells[0], "Hari/Tanggal:")
    _set_cell_plain_text(table.rows[0].cells[1], session["tanggal"])
    _set_cell_plain_text(table.rows[0].cells[2], "Tempat:")
    _set_cell_plain_text(table.rows[0].cells[3], session["tempat"])
    _set_cell_plain_text(table.rows[1].cells[0], f"Uraian: \n{session['uraian']}")
    _set_cell_plain_text(table.rows[2].cells[0], f"Rencana Pencapaian :\n{session['rencana']}")


def _update_identity_table(table) -> None:
    _set_cell_plain_text(table.rows[0].cells[2], f"{JUDUL}\n{SUB_JUDUL}")
    _set_cell_plain_text(table.rows[1].cells[2], "-")
    _set_cell_plain_text(table.rows[2].cells[2], PRODI)
    _set_cell_plain_text(table.rows[3].cells[2], NAMA)
    _set_cell_plain_text(table.rows[4].cells[2], NIM)
    _set_cell_plain_text(table.rows[5].cells[2], TA)
    _set_cell_plain_text(table.rows[6].cells[2], "-")
    _set_cell_numbered_list(table.rows[7].cells[2], TUJUAN)
    _set_cell_numbered_list(table.rows[8].cells[2], MANFAAT)


def _append_logbook_block(body, insert_at: int, prototypes: dict, session: dict, doc) -> int:
    """Satu halaman per logbook: page break → heading → tabel → tanda tangan."""
    from docx.table import Table

    tbl_elem = deepcopy(prototypes["table"])
    _fill_logbook_table(Table(tbl_elem, doc), session)

    blank = prototypes["blank"]
    elements = [
        _make_page_break_paragraph(),
        _clone_paragraph(prototypes["heading"], "Logbook/Catatan Bimbingan Proposal Skripsi"),
        _clone_empty_paragraph(blank),
        tbl_elem,
        _clone_empty_paragraph(blank),
        _clone_empty_paragraph(blank),
        _clone_paragraph(prototypes["normal"], "Mengetahui"),
        _clone_paragraph(prototypes["roles"], "Pembimbing,\tMahasiswa Pelaksana,"),
        _make_signature_spacer(1400),
        _make_signature_spacer(1400),
        _make_signature_spacer(1400),
        _clone_paragraph(prototypes["names"], f"({PEMBIMBING}) \t( {NAMA}   )"),
    ]
    return _insert_before_sectpr(body, insert_at, elements)


def build_docx() -> None:
    try:
        from docx import Document
    except ImportError as e:
        raise SystemExit("python-docx required: pip install python-docx") from e

    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")

    doc = Document(str(TEMPLATE))
    body = doc.element.body

    _update_identity_table(doc.tables[0])

    children = list(body)
    start = _find_logbook_start_index(body)
    prototypes = {
        "heading": children[start],
        "blank": children[start + 1],
        "table": doc.tables[1]._tbl,
        "normal": children[start + 5],
        "roles": children[start + 6],
        "names": children[start + 12],
    }

    end = len(body) - (1 if body[-1].tag.endswith("}sectPr") else 0)
    _remove_body_children(body, start, end)

    insert_at = start
    for session in SESSIONS:
        insert_at = _append_logbook_block(body, insert_at, prototypes, session, doc)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOCX)
    print(f"Saved: {OUT_DOCX} ({len(SESSIONS)} sesi bimbingan, format tabel template)")


def build_pdf() -> None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        print("LibreOffice (soffice) not found — skip PDF")
        return
    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(OUT_DIR),
        str(OUT_DOCX),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        print(f"Saved: {OUT_PDF}")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        err = getattr(e, "stderr", b"")
        print("PDF generation failed")
        if err:
            print(err.decode(errors="replace"))


if __name__ == "__main__":
    build_docx()
    build_pdf()
