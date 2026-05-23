"""Permission berbasis role (Django Groups)."""

from rest_framework.permissions import BasePermission

FINANCE = "Finance"
PRINCIPAL = "SchoolPrincipal"
ADMINISTRATION = "Administration"
TEACHER = "TeacherInCharge"


def _in_groups(user, groups):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=groups).exists()


class InGroup(BasePermission):
    """Subclass dan set `groups` untuk membatasi akses ke role tertentu."""

    groups: tuple = ()

    def has_permission(self, request, view):
        return _in_groups(request.user, self.groups)


class IsFinance(InGroup):
    groups = (FINANCE,)


class IsPrincipal(InGroup):
    groups = (PRINCIPAL,)


class IsAdministration(InGroup):
    groups = (ADMINISTRATION,)


class IsFinanceOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(request.user and request.user.is_authenticated)
        return _in_groups(request.user, (FINANCE,))
