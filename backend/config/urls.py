from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from accounting.api import MsCoaViewSet, TrJurnalViewSet
from operations.api import SiswaViewSet, TagihanViewSet

router = DefaultRouter()
router.register("coa", MsCoaViewSet, basename="coa")
router.register("jurnal", TrJurnalViewSet, basename="jurnal")
router.register("siswa", SiswaViewSet, basename="siswa")
router.register("tagihan", TagihanViewSet, basename="tagihan")

urlpatterns = [
    path("admin/", admin.site.urls),
    # auth (JWT)
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # resources
    path("api/", include(router.urls)),
    # docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
