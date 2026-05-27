"""Custom DRF exception handler.

Menjamin error tak terduga dari level database (mis. RAISE di trigger
PostgreSQL, pelanggaran CHECK/constraint) tetap dikembalikan sebagai 400
dengan bentuk JSON konsisten `{"detail": "..."}`, bukan 500 mentah.
Pesan ramah untuk user diterjemahkan di frontend (lihat core/errors.ts).
"""

from django.db import DatabaseError, IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, (DatabaseError, IntegrityError)):
        msg = str(exc).strip().splitlines()[0] if str(exc).strip() else "Operasi database ditolak."
        return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

    return None
