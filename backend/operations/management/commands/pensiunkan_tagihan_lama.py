"""Pensiunkan tagihan lama yang ditandai "perlu dicocokkan" beserta jurnalnya yang belum POSTED.

Dipakai sekali sebelum cut-over (keputusan pengguna 11/11/2026): tagihan BULANAN dari masa uji coba
yang pembayarannya ditautkan langsung ke jurnal (sebelum ada PembayaranTagihan) tidak bisa
direkonsiliasi lewat aplikasi, salah akun pendapatan, dan komponennya akan ditagih ulang oleh impor
biaya masuk. Siswanya ikut alur cut-over biasa setelah ini.

Default hanya menampilkan rencana. Perubahan hanya dengan --terapkan:
- jurnal tautan (AUTO_BILLING, DRAFT/PENDING) -> VOID, alasan ditambahkan ke keterangan;
- tagihan -> dihapus lunak (is_deleted), riwayat mencatat alasan.
Ditolak bila tagihan tidak bertanda perlu dicocokkan, sudah punya penerimaan baru, atau jurnalnya
sudah POSTED (itu butuh jurnal pembalik, bukan perintah ini).
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounting.models import TrJurnal
from accounting.utils import audit_user
from operations.models import Tagihan


class Command(BaseCommand):
    help = "Pensiunkan tagihan lama bertanda perlu dicocokkan beserta jurnal DRAFT/PENDING-nya."

    def add_arguments(self, parser):
        parser.add_argument("tagihan", nargs="+", type=int, help="ID tagihan, mis. 1 2 3.")
        parser.add_argument("--alasan", required=True, help="Alasan yang dicatat di jurnal dan riwayat tagihan.")
        parser.add_argument("--oleh", required=True, help="Username pelaku untuk jejak audit.")
        parser.add_argument("--terapkan", action="store_true", help="Simpan perubahan. Tanpa ini hanya rencana.")

    def handle(self, *args, **opt):
        alasan = opt["alasan"].strip()
        if not alasan:
            raise CommandError("Alasan wajib diisi.")
        try:
            pelaku = get_user_model().objects.get(username=opt["oleh"], is_active=True)
        except get_user_model().DoesNotExist:
            raise CommandError(f"User aktif {opt['oleh']!r} tidak ditemukan.")

        with transaction.atomic(), audit_user(pelaku):
            ids = sorted(set(opt["tagihan"]))
            daftar = list(Tagihan.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
            ditemukan = {t.pk for t in daftar}
            masalah = [f"tagihan {i}: tidak ada atau sudah dihapus" for i in ids if i not in ditemukan]
            rencana = []
            for t in daftar:
                jurnal = TrJurnal.objects.select_for_update().filter(pk=t.jurnal_id).first() if t.jurnal_id else None
                if not t.perlu_rekonsiliasi:
                    masalah.append(f"tagihan {t.pk}: tidak bertanda perlu dicocokkan")
                elif t.pembayaran.exists():
                    masalah.append(f"tagihan {t.pk}: sudah punya penerimaan baru")
                elif jurnal and (jurnal.tipe_sumber != "AUTO_BILLING" or jurnal.status not in ("DRAFT", "PENDING")):
                    masalah.append(f"tagihan {t.pk}: jurnal {jurnal.no_bukti} {jurnal.tipe_sumber}/{jurnal.status} tidak bisa dibatalkan di sini")
                else:
                    rencana.append((t, jurnal))
            if masalah:
                raise CommandError("Dibatalkan, tidak ada yang diubah:\n- " + "\n- ".join(masalah))

            for t, jurnal in rencana:
                info = f"jurnal {jurnal.no_bukti} {jurnal.status} -> VOID" if jurnal else "tanpa jurnal"
                self.stdout.write(f"tagihan {t.pk} (siswa {t.siswa_id}, {t.periode_bulan}/{t.periode_tahun}, {t.jenis}, {t.status}) -> dihapus; {info}")
            if not opt["terapkan"]:
                self.stdout.write(self.style.WARNING(f"Rencana saja ({len(rencana)} tagihan). Jalankan lagi dengan --terapkan."))
                transaction.set_rollback(True)
                return

            for t, jurnal in rencana:
                if jurnal:
                    jurnal.status = "VOID"
                    jurnal.keterangan = f"{jurnal.keterangan or ''}\nDipensiunkan: {alasan}".strip()
                    jurnal.save(update_fields=["status", "keterangan"])
                t._change_reason = f"Dipensiunkan: {alasan}"
                t.delete()
        self.stdout.write(self.style.SUCCESS(f"Selesai: {len(rencana)} tagihan dipensiunkan."))
