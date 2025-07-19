from django.urls import path
from .views import landing, CustomLoginView, no_permission_view,dashboard_view  # ← perbaikan di sini
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView

urlpatterns = [
    path('', landing, name='landing'),
    path('login/', CustomLoginView.as_view(), name='login'),

    # path('login/', RedirectView.as_view(url='https://beesmartfinance.online/#contact', permanent=False)),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('no-permission/', no_permission_view, name='no_permission'),
    path('dashboard/', dashboard_view, name='dashboard'),
]
