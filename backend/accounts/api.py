"""API akun: info user yang sedang login (untuk RBAC di frontend)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


@extend_schema(responses=OpenApiTypes.OBJECT)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "nama": u.get_full_name() or u.username,
            "is_superuser": u.is_superuser,
            "groups": list(u.groups.values_list("name", flat=True)),
        })
