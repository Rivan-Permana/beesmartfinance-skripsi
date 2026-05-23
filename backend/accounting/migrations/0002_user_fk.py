from pathlib import Path

from django.db import migrations

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "database" / "schemas"
_SQL_FORWARD = (_SCHEMA_DIR / "03_user_fk.sql").read_text(encoding="utf-8")
_SQL_REVERSE = """
ALTER TABLE tr_jurnal DROP CONSTRAINT IF EXISTS fk_jurnal_created_by;
ALTER TABLE tr_jurnal DROP CONSTRAINT IF EXISTS fk_jurnal_submitted_by;
ALTER TABLE tr_jurnal DROP CONSTRAINT IF EXISTS fk_jurnal_approved_by;
ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS fk_audit_changed_by;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("accounting", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=_SQL_FORWARD, reverse_sql=_SQL_REVERSE),
    ]
