from contextlib import contextmanager

from django.db import connection


@contextmanager
def audit_user(user):
    """Kirim user aplikasi ke sesi DB agar trigger audit mencatat pelakunya.

    set_config(..., is_local=true) setara SET LOCAL — hanya berlaku dalam
    transaksi berjalan, jadi panggil di dalam transaction.atomic().
    """
    user_id = "" if user is None else str(getattr(user, "pk", "") or "")
    with connection.cursor() as cur:
        cur.execute("SELECT set_config('app.current_user_id', %s, true)", [user_id])
    yield
