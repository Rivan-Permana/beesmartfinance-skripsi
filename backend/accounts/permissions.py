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


class IsFinanceOrPrincipal(InGroup):
    groups = (FINANCE, PRINCIPAL)


class IsTeacherOrPrincipal(InGroup):
    groups = (TEACHER, PRINCIPAL)


class IsAdministrationOrTeacherReadOnly(BasePermission):
    """Admin tulis; TeacherInCharge baca saja (rekap absensi)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return _in_groups(request.user, (ADMINISTRATION, TEACHER))
        return _in_groups(request.user, (ADMINISTRATION,))


class IsAdministrationOrFinance(InGroup):
    groups = (ADMINISTRATION, FINANCE)


class IsAdministrationOrFinanceOrPrincipalRead(BasePermission):
    """Master pegawai: Admin/Finance kelola; Principal baca (oversight)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return _in_groups(request.user, (ADMINISTRATION, FINANCE, PRINCIPAL))
        return _in_groups(request.user, (ADMINISTRATION, FINANCE))


class IsAdministrationWriteFinancePrincipalRead(BasePermission):
    """Tagihan: Admin bayar/tulis; Finance/Principal baca tunggakan."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return _in_groups(request.user, (ADMINISTRATION, FINANCE, PRINCIPAL))
        return _in_groups(request.user, (ADMINISTRATION,))


class IsFinanceWriteFinancePrincipalRead(BasePermission):
    """Data sensitif (gaji/pinjaman): baca = Finance/Principal, tulis = Finance."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return _in_groups(request.user, (FINANCE, PRINCIPAL))
        return _in_groups(request.user, (FINANCE,))
