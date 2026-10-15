import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import DatabaseError, transaction
from rest_framework.test import APITestCase

from accounting.models import AuditLog, MsCoa, MsPeriodeAkuntansi, TrJurnal, TrJurnalDetail
from accounting.reports import _saldo_tahun
from accounting.services import close_period


class OpeningBalanceTests(APITestCase):
    def setUp(self):
        self.finance = get_user_model().objects.create_user("opening-finance")
        self.finance.groups.add(Group.objects.get(name="Finance"))
        self.client.force_authenticate(self.finance)
        self.cash = MsCoa.objects.create(kode_akun="111", nama_akun="Kas", posisi_normal="D")
        self.capital = MsCoa.objects.create(kode_akun="311", nama_akun="Modal", posisi_normal="K")

    def opening(self, account=None, value="1000.25", on="2025-01-01"):
        account = account or self.cash
        return self.client.patch(f"/api/v1/coa/{account.pk}/", {
            "saldo_awal": value, "tanggal_saldo_awal": on,
        }, format="json")

    def posted(self, on=date(2026, 2, 1), value=100):
        jurnal = TrJurnal.objects.create(id=uuid.uuid4(), no_bukti=str(uuid.uuid4()), tanggal=on)
        TrJurnalDetail.objects.create(jurnal=jurnal, kode_akun=self.cash, debit=value)
        TrJurnalDetail.objects.create(jurnal=jurnal, kode_akun=self.capital, kredit=value)
        jurnal.status = "POSTED"
        jurnal.save(update_fields=["status"])
        return jurnal

    def test_create_and_edit_opening_balance_and_audit_actor(self):
        response = self.client.post("/api/v1/coa/", {
            "kode_akun": "112", "nama_akun": "Bank", "posisi_normal": "D",
            "saldo_awal": "123.45", "tanggal_saldo_awal": "2026-01-01",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["saldo_awal"], "123.45")
        self.assertEqual(self.opening(value="456.78").status_code, 200)
        entry = AuditLog.objects.filter(table_name="ms_coa", row_pk="111").latest("id")
        self.assertEqual(entry.changed_by_id, self.finance.pk)
        self.assertEqual(Decimal(str(entry.new_data["saldo_awal"])), Decimal("456.78"))
        self.assertEqual(entry.old_data["created_at"], entry.new_data["created_at"])

    def test_nonzero_opening_requires_date_and_valid_precision(self):
        self.assertEqual(self.opening(on=None).status_code, 400)
        self.assertEqual(self.opening(value="1.234").status_code, 400)
        self.cash.refresh_from_db()
        self.assertEqual(self.cash.saldo_awal, 0)
        self.assertIsNone(self.cash.tanggal_saldo_awal)

    def test_balance_is_carried_across_years_without_a_cash_transaction(self):
        self.assertEqual(self.opening().status_code, 200)
        self.assertEqual(self.opening(self.capital).status_code, 200)
        self.posted()
        balances = {r["kode_akun"]: r for r in _saldo_tahun(2026, kumulatif=True)}
        self.assertEqual(balances["111"]["saldo_akhir"], Decimal("1100.25"))
        self.assertEqual(balances["311"]["saldo_akhir"], Decimal("1100.25"))
        self.assertEqual(balances["311"]["total_kredit"], Decimal("1100.25"))
        dashboard = self.client.get("/api/v1/dashboard/ringkasan/?tahun=2026&bulan=2")
        self.assertEqual(dashboard.status_code, 200, dashboard.data)
        self.assertEqual(Decimal(str(dashboard.data["kas"])), Decimal("1100.25"))
        self.assertEqual(TrJurnal.objects.count(), 1)
        self.assertEqual(self.client.get("/api/v1/laporan/neraca-saldo/?tahun=2026").data[0]["saldo_akhir"], Decimal("1100.25"))

    def test_future_opening_does_not_affect_earlier_report(self):
        self.assertEqual(self.opening(on="2027-01-01").status_code, 200)
        earlier = {r["kode_akun"]: r for r in _saldo_tahun(2026, kumulatif=True)}
        self.assertEqual(earlier["111"]["saldo_akhir"], 0)

    def test_credit_and_negative_normal_balances(self):
        self.assertEqual(self.opening(self.capital, value="-25.50").status_code, 200)
        result = {r["kode_akun"]: r for r in _saldo_tahun(2026, kumulatif=True)}["311"]
        self.assertEqual(result["total_debit"], Decimal("25.50"))
        self.assertEqual(result["saldo_akhir"], Decimal("-25.50"))

    def test_ledger_carries_balance_into_selected_month(self):
        self.opening()
        self.posted(on=date(2025, 12, 1), value=100)
        self.posted(value=20)
        response = self.client.get("/api/v1/laporan/buku-besar/111/?tahun=2026&bulan=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["no_bukti"], "SALDO-AWAL")
        self.assertEqual(response.data[0]["debit"], Decimal("1100.25"))
        self.assertEqual(sum(r["debit"] - r["kredit"] for r in response.data), Decimal("1120.25"))

    def test_mid_month_opening_is_in_ledger_before_same_day_transaction(self):
        self.opening(on="2026-02-10")
        self.posted(on=date(2026, 2, 10))
        rows = self.client.get("/api/v1/laporan/buku-besar/111/?tahun=2026&bulan=2").data
        self.assertEqual(rows[0]["no_bukti"], "SALDO-AWAL")
        self.assertEqual(sum(r["debit"] - r["kredit"] for r in rows), Decimal("1100.25"))

    def test_opening_cannot_replace_existing_posted_history(self):
        self.posted()
        self.assertEqual(self.opening(on="2026-03-01").status_code, 400)
        self.cash.refresh_from_db()
        self.assertEqual(self.cash.saldo_awal, 0)

    def test_backdated_posting_before_opening_is_rejected(self):
        self.opening(on="2026-03-01")
        with self.assertRaises(DatabaseError), transaction.atomic():
            self.posted()

    def test_closed_opening_cannot_be_changed_or_cleared(self):
        self.opening()
        MsPeriodeAkuntansi.objects.create(kode="2025", tgl_mulai=date(2025, 1, 1), tgl_selesai=date(2025, 12, 31), status="CLOSED")
        self.assertEqual(self.opening(value="2000", on="2026-01-01").status_code, 400)
        self.assertEqual(self.opening(value="0", on=None).status_code, 400)
        self.assertEqual(self.client.delete("/api/v1/coa/111/").status_code, 400)

    def test_read_only_role_cannot_edit_opening(self):
        user = get_user_model().objects.create_user("opening-principal")
        user.groups.add(Group.objects.get(name="SchoolPrincipal"))
        self.client.force_authenticate(user)
        self.assertEqual(self.opening().status_code, 403)

    def test_income_opening_is_closed_into_equity(self):
        income = MsCoa.objects.create(kode_akun="411", nama_akun="SPP", posisi_normal="K")
        equity = MsCoa.objects.create(kode_akun="3102", nama_akun="Laba ditahan", posisi_normal="K")
        self.opening(income, value="500", on="2026-01-01")
        period = MsPeriodeAkuntansi.objects.create(kode="2026", tgl_mulai=date(2026, 1, 1), tgl_selesai=date(2026, 12, 31))
        dashboard = self.client.get("/api/v1/dashboard/ringkasan/?tahun=2026")
        self.assertEqual(Decimal(str(dashboard.data["total_pendapatan"])), 0)
        close_period(period, user=self.finance, akun_ekuitas=equity.pk)
        balances = {r["kode_akun"]: r for r in _saldo_tahun(2027, kumulatif=True)}
        self.assertEqual(balances["411"]["saldo_akhir"], 0)
        self.assertEqual(balances["3102"]["saldo_akhir"], 500)
