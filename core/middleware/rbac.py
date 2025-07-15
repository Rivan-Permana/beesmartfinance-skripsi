from django.shortcuts import redirect
from django.urls import resolve
from django.conf import settings

class RBACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- KECUALIKAN URL ADMIN DAN STATIK ---
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)

        # --- KECUALIKAN JIKA BELUM LOGIN ---
        if not request.user.is_authenticated:
            return self.get_response(request)

        # --- AMBIL NAMA URL ---
        try:
            resolver_match = resolve(request.path)
            url_name = resolver_match.url_name
        except:
            return self.get_response(request)

        # --- CARI APAKAH URL NAME DIIJINKAN UNTUK GRUP USER ---
        if request.user.groups.exists():
            allowed = request.user.groups.filter(
                roleurlaccess__url_name=url_name
            ).exists()
            if not allowed:
                return redirect('no_permission')  # arahkan ke view khusus
        return self.get_response(request)
