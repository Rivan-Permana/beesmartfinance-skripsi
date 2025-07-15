from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

# Halaman utama (public)
def landing(request):
    return render(request, 'landing.html')

# Login view
class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('dashboard')

    def get_success_url(self):
        return self.success_url

# Dashboard, hanya bisa diakses user yang login
@login_required
def dashboard_view(request):
    return render(request, 'backend/dashboard.html')

# Logout yang bisa pakai metode GET (untuk tombol <a href>)
class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

# Halaman jika user tidak punya akses (RBAC)
def no_permission_view(request):
    return render(request, 'no_permission.html')
