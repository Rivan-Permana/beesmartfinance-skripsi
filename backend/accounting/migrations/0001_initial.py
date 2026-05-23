from pathlib import Path

from django.db import migrations, models

# Raw SQL kanonik milik core accounting (single source of truth).
# Diterapkan via RunSQL agar DB test/dev identik dengan produksi.
_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "database" / "schemas"
_SQL_FORWARD = (
    (_SCHEMA_DIR / "01_init_schema.sql").read_text(encoding="utf-8")
    + "\n"
    + (_SCHEMA_DIR / "02_governance.sql").read_text(encoding="utf-8")
)
_SQL_REVERSE = """
DROP VIEW IF EXISTS v_realisasi_anggaran;
DROP VIEW IF EXISTS v_dataset_prediksi_kas;
DROP VIEW IF EXISTS v_neraca_saldo;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS tr_jurnal_detail CASCADE;
DROP TABLE IF EXISTS tr_anggaran CASCADE;
DROP TABLE IF EXISTS tr_jurnal CASCADE;
DROP TABLE IF EXISTS ms_coa CASCADE;
DROP TABLE IF EXISTS ms_sub_golongan CASCADE;
DROP TABLE IF EXISTS ms_golongan CASCADE;
DROP TABLE IF EXISTS ms_periode_akuntansi CASCADE;
DROP FUNCTION IF EXISTS fn_audit() CASCADE;
DROP FUNCTION IF EXISTS fn_protect_posted_jurnal() CASCADE;
DROP FUNCTION IF EXISTS fn_protect_posted_detail() CASCADE;
DROP FUNCTION IF EXISTS fn_check_post_rules() CASCADE;
"""


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("table_name", models.TextField()),
                ("row_pk", models.TextField(blank=True, null=True)),
                ("action", models.CharField(max_length=10)),
                ("old_data", models.JSONField(blank=True, null=True)),
                ("new_data", models.JSONField(blank=True, null=True)),
                ("changed_at", models.DateTimeField()),
            ],
            options={
                "db_table": "audit_log",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="MsCoa",
            fields=[
                (
                    "kode_akun",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("nama_akun", models.CharField(max_length=255)),
                (
                    "posisi_normal",
                    models.CharField(
                        choices=[("D", "Debit"), ("K", "Kredit")], max_length=1
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ms_coa",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="MsGolongan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("kode_golongan", models.CharField(max_length=5, unique=True)),
                ("nama_golongan", models.CharField(max_length=50)),
                ("deskripsi", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "ms_golongan",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="MsPeriodeAkuntansi",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("kode", models.CharField(max_length=20, unique=True)),
                ("tgl_mulai", models.DateField()),
                ("tgl_selesai", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("OPEN", "Open"), ("CLOSED", "Closed")],
                        default="OPEN",
                        max_length=10,
                    ),
                ),
            ],
            options={
                "db_table": "ms_periode_akuntansi",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="MsSubGolongan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("kode_sub", models.CharField(max_length=10, unique=True)),
                ("nama_sub", models.CharField(max_length=100)),
            ],
            options={
                "db_table": "ms_sub_golongan",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="TrAnggaran",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tahun_anggaran", models.IntegerField()),
                ("bulan", models.IntegerField(blank=True, null=True)),
                (
                    "nominal_anggaran",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                ("keterangan", models.TextField(blank=True, null=True)),
                ("carry_over", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "tr_anggaran",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="TrJurnal",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("no_bukti", models.CharField(max_length=50, unique=True)),
                ("tanggal", models.DateField()),
                ("keterangan", models.TextField(blank=True, null=True)),
                ("tipe_sumber", models.CharField(default="MANUAL", max_length=20)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Draft"),
                            ("PENDING", "Pending"),
                            ("POSTED", "Posted"),
                            ("VOID", "Void"),
                        ],
                        default="DRAFT",
                        max_length=10,
                    ),
                ),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "tr_jurnal",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="TrJurnalDetail",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "debit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "kredit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
            ],
            options={
                "db_table": "tr_jurnal_detail",
                "managed": False,
            },
        ),
        # DDL nyata (tabel, constraint, trigger, view) dari raw SQL kanonik.
        # CreateModel di atas managed=False -> tidak menerbitkan DDL; RunSQL ini
        # yang benar-benar membangun skema core di database.
        migrations.RunSQL(sql=_SQL_FORWARD, reverse_sql=_SQL_REVERSE),
    ]
