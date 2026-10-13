"""Custom DRF exception handler.

Menjamin error tak terduga dari level database tetap dikembalikan sebagai 400
dengan bentuk JSON konsisten `{"detail": "..."}` dan pesan ramah berbahasa Indonesia.
"""

from django.db import DatabaseError, IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from config.db_errors import humanize_db_error


def _humanize_response_data(data):
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, str):
            data = {**data, "detail": humanize_db_error(detail)}
        elif isinstance(detail, list):
            data = {
                **data,
                "detail": humanize_db_error(" · ".join(str(x) for x in detail)),
            }
    return data


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = _humanize_response_data(response.data)
        return response

    if isinstance(exc, (DatabaseError, IntegrityError)):
        msg = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
        return Response(
            {"detail": humanize_db_error(msg)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None
