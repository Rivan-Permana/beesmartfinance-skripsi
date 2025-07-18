from django.urls import path
from .views import landing, CustomLoginView, no_permission_view,dashboard_view  # ← perbaikan di sini
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', landing, name='landing'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('no-permission/', no_permission_view, name='no_permission'),
    path('dashboard/', dashboard_view, name='dashboard'),
]
