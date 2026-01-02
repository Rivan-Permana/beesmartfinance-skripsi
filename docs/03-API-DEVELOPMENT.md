# 🔌 API Development Guide

> Panduan lengkap pembangunan RESTful API dengan Django REST Framework

## Quick Setup

```bash
pip install djangorestframework djangorestframework-simplejwt drf-spectacular django-filter django-cors-headers
```

## Configuration

```python
# settings.py
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative
]

# Spectacular (API Documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Beesmartfinance API',
    'DESCRIPTION': 'API untuk Sistem Manajemen TK Lebah Madu',
    'VERSION': '1.0.0',
}
```

## Serializers

```python
# siswa/serializers.py
from rest_framework import serializers
from .models import Siswa, Kelompok, Kehadiran

class KelompokSerializer(serializers.ModelSerializer):
    jenjang_nama = serializers.CharField(source='jenjang.nama', read_only=True)
    
    class Meta:
        model = Kelompok
        fields = ['id', 'nama', 'jenjang', 'jenjang_nama']

class SiswaSerializer(serializers.ModelSerializer):
    kelompok_detail = KelompokSerializer(source='kelompok', read_only=True)
    usia = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Siswa
        fields = [
            'id', 'nis', 'nama', 'tanggal_lahir', 'alamat',
            'kelompok', 'kelompok_detail', 'periode',
            'nama_ayah', 'kontak_ayah', 'nama_ibu', 'kontak_ibu',
            'spp', 'status', 'usia', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class KehadiranSerializer(serializers.ModelSerializer):
    siswa_nama = serializers.CharField(source='siswa.nama', read_only=True)
    
    class Meta:
        model = Kehadiran
        fields = '__all__'
```

## ViewSets

```python
# siswa/viewsets.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Siswa, Kehadiran
from .serializers import SiswaSerializer, KehadiranSerializer

class SiswaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Siswa CRUD operations.
    
    list: Get all students
    retrieve: Get single student
    create: Create new student
    update: Update student
    partial_update: Partial update student
    destroy: Delete student
    """
    queryset = Siswa.objects.select_related('kelompok', 'kelompok__jenjang', 'periode')
    serializer_class = SiswaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'kelompok', 'periode']
    search_fields = ['nis', 'nama', 'nama_ayah', 'nama_ibu']
    ordering_fields = ['nis', 'nama', 'created_at']
    ordering = ['nama']

    @action(detail=True, methods=['get'])
    def kehadiran(self, request, pk=None):
        """Get attendance records for student"""
        siswa = self.get_object()
        kehadiran = Kehadiran.objects.filter(siswa=siswa).order_by('-tanggal')
        serializer = KehadiranSerializer(kehadiran, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get student statistics"""
        from django.db.models import Count, Q
        
        stats = Siswa.objects.aggregate(
            total=Count('id'),
            aktif=Count('id', filter=Q(status='aktif')),
            lulus=Count('id', filter=Q(status='lulus')),
            cuti=Count('id', filter=Q(status='cuti')),
        )
        return Response(stats)
```

## URLs

```python
# penelitian_tk/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from siswa.viewsets import SiswaViewSet
from pegawai.viewsets import PegawaiViewSet
from keuangan.viewsets import KeuanganViewSet

# Router
router = DefaultRouter()
router.register('siswa', SiswaViewSet, basename='siswa')
router.register('pegawai', PegawaiViewSet, basename='pegawai')
router.register('keuangan', KeuanganViewSet, basename='keuangan')

urlpatterns = [
    # API
    path('api/', include(router.urls)),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

## Authentication

```python
# core/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['groups'] = list(user.groups.values_list('name', flat=True))
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'groups': list(self.user.groups.values_list('name', flat=True)),
        }
        
        return data
```

## Testing API

```python
# siswa/tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from siswa.models import Siswa, Kelompok, Jenjang

class SiswaAPITest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='test', password='test123')
        self.client.force_authenticate(user=self.user)
        
        self.jenjang = Jenjang.objects.create(kode='TK', nama='TK')
        self.kelompok = Kelompok.objects.create(jenjang=self.jenjang, nama='A')

    def test_list_siswa(self):
        response = self.client.get('/api/siswa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_siswa(self):
        data = {
            'nis': '001',
            'nama': 'Test Student',
            'kelompok': self.kelompok.id,
            'spp': 500000,
        }
        response = self.client.post('/api/siswa/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Siswa.objects.count(), 1)
```

---

**Last Updated**: 2025-12-28
