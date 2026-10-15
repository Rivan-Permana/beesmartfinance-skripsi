"""Service layer auto-posting, dipecah per domain.

Re-export agar `from operations.services import fn` tetap berfungsi.
"""

from .common import akun_rule, audit_user, buat_jurnal
from .billing import (
    generate_batch_tagihan,
    generate_tagihan,
    post_pembayaran_tagihan,
    preview_batch_tagihan,
    preview_tagihan,
    struk_tagihan,
)
from .payroll import post_gaji, post_pencairan_kasbon
from .assets import post_penyusutan
from .activities import post_realisasi_kegiatan
from .registration import finalisasi_pendaftaran, post_bayar_sitin, post_pembayaran_pendaftaran

__all__ = [
    "akun_rule", "audit_user", "buat_jurnal",
    "generate_tagihan", "generate_batch_tagihan", "post_pembayaran_tagihan",
    "preview_tagihan", "preview_batch_tagihan", "struk_tagihan",
    "post_gaji", "post_pencairan_kasbon",
    "post_penyusutan",
    "post_realisasi_kegiatan",
    "finalisasi_pendaftaran", "post_bayar_sitin", "post_pembayaran_pendaftaran",
]
