# 🔧 Backend Refactoring Guide

> Panduan lengkap untuk refactoring backend Django

## 📑 Table of Contents

- [Overview](#overview)
- [Phase 1: Security Hardening](#phase-1-security-hardening)
- [Phase 2: Code Architecture](#phase-2-code-architecture)
- [Phase 3: Database Optimization](#phase-3-database-optimization)
- [Phase 4: Error Handling & Logging](#phase-4-error-handling--logging)
- [Phase 5: Service Layer Pattern](#phase-5-service-layer-pattern)
- [Best Practices](#best-practices)

---

## Overview

### Goals
- ✅ Improve code security
- ✅ Enhance maintainability
- ✅ Optimize performance
- ✅ Enable scalability
- ✅ Prepare for API development

### Timeline
- **Phase 1**: 1 week (Security)
- **Phase 2**: 2 weeks (Architecture)
- **Phase 3**: 1 week (Database)
- **Phase 4**: 1 week (Logging)
- **Phase 5**: 2 weeks (Service Layer)
- **Total**: 7 weeks

---

## Phase 1: Security Hardening

### 1.1 Environment Variables

#### Step 1: Install python-decouple

```bash
pip install python-decouple
```

#### Step 2: Create .env file

```bash
# .env
DEBUG=False
SECRET_KEY=your-secret-key-here-generate-new-one
DATABASE_URL=postgresql://user:password@localhost:5432/beesmartfinance
ALLOWED_HOSTS=localhost,127.0.0.1,.yourdomain.com

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis
REDIS_URL=redis://localhost:6379/1

# Sentry (Error Tracking)
SENTRY_DSN=your-sentry-dsn

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### Step 3: Update settings.py

```python
# penelitian_tk/settings.py
from decouple import config, Csv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = config('SECRET_KEY')  # No fallback!
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

#### Step 4: Add .env to .gitignore

```bash
# .gitignore
.env
.env.local
.env.*.local
*.sqlite3
db.sqlite3
```

#### Step 5: Create .env.example

```bash
# .env.example
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
ALLOWED_HOSTS=localhost,127.0.0.1
# ... (all keys without values)
```

### 1.2 Security Headers

```python
# settings.py

# Security Settings (Production)
if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Cookies
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Strict'

    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Content Security
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# Password Validation (Enhanced)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,  # Increased from 8
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### 1.3 Rate Limiting

#### Install django-ratelimit

```bash
pip install django-ratelimit
```

#### Apply to login view

```python
# core/views.py
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache

@never_cache
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """
    Login view with rate limiting.
    Max 5 attempts per minute per IP.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Log successful login
            logger.info(f"Successful login: {username} from {request.META.get('REMOTE_ADDR')}")

            return redirect('dashboard')
        else:
            # Log failed login attempt
            logger.warning(f"Failed login attempt: {username} from {request.META.get('REMOTE_ADDR')}")

            messages.error(request, 'Username atau password salah')

    return render(request, 'login.html')

# Alternative: Using CBV
from django.contrib.auth.views import LoginView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        logger.info(f"Successful login: {form.cleaned_data.get('username')}")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f"Failed login attempt from {self.request.META.get('REMOTE_ADDR')}")
        return super().form_invalid(form)
```

### 1.4 Input Validation & Sanitization

```python
# core/validators.py
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

def validate_phone_number(value):
    """
    Validate Indonesian phone number format.
    Accepts: +62xxx, 62xxx, 08xxx
    """
    pattern = r'^(\+62|62|0)[0-9]{9,12}$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Format nomor telepon tidak valid. Gunakan format: +62xxx, 62xxx, atau 08xxx'
        )

def validate_nis(value):
    """Validate NIS format (numbers only, max 20 chars)"""
    if not value.isdigit():
        raise ValidationError('NIS harus berupa angka')
    if len(value) > 20:
        raise ValidationError('NIS maksimal 20 karakter')

def validate_nik(value):
    """Validate NIK (16 digits)"""
    if not value.isdigit():
        raise ValidationError('NIK harus berupa angka')
    if len(value) != 16:
        raise ValidationError('NIK harus 16 digit')

# Usage in models
class Siswa(models.Model):
    nis = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_nis]
    )
    kontak_ayah = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone_number]
    )
```

### 1.5 SQL Injection Prevention

**Already Protected**: Django ORM uses parameterized queries by default.

**Warning**: Avoid raw SQL when possible. If needed, use parameterized queries:

```python
# ❌ NEVER do this
def get_siswa_unsafe(nis):
    query = f"SELECT * FROM siswa WHERE nis = '{nis}'"  # SQL Injection!
    return Siswa.objects.raw(query)

# ✅ Safe approach - Use ORM
def get_siswa_safe(nis):
    return Siswa.objects.filter(nis=nis)

# ✅ If you must use raw SQL, use parameters
def get_siswa_raw(nis):
    query = "SELECT * FROM siswa WHERE nis = %s"
    return Siswa.objects.raw(query, [nis])
```

### 1.6 XSS Prevention

**Already Protected**: Django templates auto-escape by default.

```django
{# ✅ Auto-escaped - Safe #}
<p>{{ user_input }}</p>

{# ⚠️ Bypasses escaping - Use with caution #}
<p>{{ html_content|safe }}</p>

{# ✅ Better approach for HTML content #}
{% autoescape off %}
  {{ html_content }}  {# Only if you control the source #}
{% endautoescape %}
```

**For JSON in templates**:

```django
{# ❌ Unsafe #}
<script>
  var data = {{ json_data|safe }};
</script>

{# ✅ Safe #}
<script>
  var data = JSON.parse('{{ json_data|escapejs }}');
</script>
```

### 1.7 CSRF Protection

**Already Implemented**: CSRF tokens in all forms.

**Additional Security**:

```python
# settings.py
CSRF_USE_SESSIONS = True  # Store CSRF token in session
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# For AJAX requests
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
```

**JavaScript for AJAX**:

```javascript
// static/js/csrf.js
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Use in fetch/axios
fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
});
```

---

## Phase 2: Code Architecture

### 2.1 Migrate to Class-Based Views

#### Before (Function-Based View)

```python
# siswa/views.py (OLD)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Siswa
from .forms import SiswaForm

@login_required
def daftar_siswa(request):
    siswa_list = Siswa.objects.select_related("kelompok", "kelompok__jenjang").all()
    return render(request, "siswa/daftar.html", {"siswa_list": siswa_list})

@login_required
def tambah_siswa(request):
    form = SiswaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Data siswa berhasil ditambahkan.")
        return redirect("daftar_siswa")
    return render(request, "siswa/form.html", {"form": form})

@login_required
def edit_siswa(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    form = SiswaForm(request.POST or None, instance=siswa)
    if form.is_valid():
        form.save()
        messages.success(request, "Data siswa berhasil diubah.")
        return redirect("daftar_siswa")
    return render(request, "siswa/form.html", {"form": form, "siswa": siswa})

@login_required
def hapus_siswa(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    siswa.delete()
    messages.success(request, "Data siswa berhasil dihapus.")
    return redirect("daftar_siswa")
```

#### After (Class-Based Views)

```python
# siswa/views.py (NEW)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Siswa
from .forms import SiswaForm

class SiswaListView(LoginRequiredMixin, ListView):
    """Display list of all students"""
    model = Siswa
    template_name = "siswa/daftar.html"
    context_object_name = "siswa_list"
    paginate_by = 25

    def get_queryset(self):
        queryset = Siswa.objects.select_related(
            "kelompok",
            "kelompok__jenjang",
            "periode"
        )

        # Add filtering
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Add search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(nis__icontains=search) |
                models.Q(nama__icontains=search)
            )

        return queryset.order_by('nama')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Daftar Siswa'
        context['status_choices'] = Siswa.STATUS_CHOICES
        return context


class SiswaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create new student"""
    model = Siswa
    form_class = SiswaForm
    template_name = "siswa/form.html"
    success_url = reverse_lazy("siswa:list")
    success_message = "Data siswa %(nama)s berhasil ditambahkan."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tambah Siswa'
        context['action'] = 'create'
        return context


class SiswaUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update existing student"""
    model = Siswa
    form_class = SiswaForm
    template_name = "siswa/form.html"
    success_url = reverse_lazy("siswa:list")
    success_message = "Data siswa %(nama)s berhasil diubah."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Siswa'
        context['action'] = 'update'
        return context


class SiswaDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete student"""
    model = Siswa
    template_name = "siswa/confirm_delete.html"
    success_url = reverse_lazy("siswa:list")
    success_message = "Data siswa berhasil dihapus."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class SiswaDetailView(LoginRequiredMixin, DetailView):
    """Display student details"""
    model = Siswa
    template_name = "siswa/detail.html"
    context_object_name = "siswa"

    def get_queryset(self):
        return Siswa.objects.select_related(
            "kelompok",
            "kelompok__jenjang",
            "periode"
        ).prefetch_related(
            "kehadiran_set",
            "kateringentry_set",
            "siswakatering_set"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        siswa = self.object

        # Add related data
        context['total_kehadiran'] = siswa.kehadiran_set.count()
        context['kehadiran_hadir'] = siswa.kehadiran_set.filter(
            kehadiran='hadir'
        ).count()

        return context
```

#### Update URLs

```python
# siswa/urls.py (NEW)
from django.urls import path
from . import views

app_name = 'siswa'

urlpatterns = [
    path('', views.SiswaListView.as_view(), name='list'),
    path('create/', views.SiswaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SiswaDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.SiswaUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.SiswaDeleteView.as_view(), name='delete'),
]
```

### 2.2 Custom Mixins for Reusability

```python
# core/mixins.py
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

class GroupRequiredMixin(UserPassesTestMixin):
    """
    Mixin to check if user belongs to specific group(s).

    Usage:
        class MyView(GroupRequiredMixin, ListView):
            group_required = 'admin'  # or ['admin', 'staff']
    """
    group_required = None

    def test_func(self):
        if self.group_required is None:
            return True

        user = self.request.user
        if not user.is_authenticated:
            return False

        if isinstance(self.group_required, str):
            groups = [self.group_required]
        else:
            groups = self.group_required

        return user.groups.filter(name__in=groups).exists()

    def handle_no_permission(self):
        messages.error(self.request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('no_permission')


class AuditMixin:
    """
    Mixin to automatically add created_by and updated_by fields.

    Model must have these fields:
    - created_by (ForeignKey to User)
    - updated_by (ForeignKey to User)
    """

    def form_valid(self, form):
        if not form.instance.pk:
            # Creating new object
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class SoftDeleteMixin:
    """
    Mixin for soft delete (mark as deleted instead of actually deleting).

    Model must have:
    - is_deleted (BooleanField)
    - deleted_at (DateTimeField)
    """

    def delete(self, request, *args, **kwargs):
        from django.utils import timezone

        self.object = self.get_object()
        self.object.is_deleted = True
        self.object.deleted_at = timezone.now()
        self.object.save()

        return redirect(self.get_success_url())


class ExportMixin:
    """
    Mixin to add export functionality to ListView.

    Usage:
        ?export=csv or ?export=excel
    """

    def render_to_response(self, context, **response_kwargs):
        export_format = self.request.GET.get('export')

        if export_format == 'csv':
            return self.export_csv(context)
        elif export_format == 'excel':
            return self.export_excel(context)

        return super().render_to_response(context, **response_kwargs)

    def export_csv(self, context):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.model.__name__}.csv"'

        writer = csv.writer(response)

        # Header
        fields = [f.name for f in self.model._meta.fields]
        writer.writerow(fields)

        # Data
        for obj in context['object_list']:
            writer.writerow([getattr(obj, f) for f in fields])

        return response

    def export_excel(self, context):
        # Implement Excel export using openpyxl
        pass


# Usage Example
class SiswaListView(LoginRequiredMixin, GroupRequiredMixin, ExportMixin, ListView):
    model = Siswa
    group_required = ['admin', 'guru']
    # ... rest of the code
```

### 2.3 Improve RBAC Middleware

```python
# core/middleware/rbac.py (IMPROVED)
import logging
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from core.models import RoleURLAccess

logger = logging.getLogger(__name__)

class ImprovedRBACMiddleware(MiddlewareMixin):
    """
    Improved Role-Based Access Control Middleware with:
    - Proper error handling
    - Caching for performance
    - Logging for audit
    - Excluded URLs configuration
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.excluded_urls = [
            'login',
            'logout',
            'no_permission',
            'password_reset',
            'password_reset_done',
            'password_reset_confirm',
            'password_reset_complete',
        ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check access before view is called.
        """
        # Skip if not authenticated
        if not request.user.is_authenticated:
            return None

        # Superusers have access to everything
        if request.user.is_superuser:
            return None

        # Get URL name
        url_name = request.resolver_match.url_name if request.resolver_match else None

        # Skip excluded URLs
        if url_name in self.excluded_urls:
            return None

        # Check access
        if not self._has_access(request.user, url_name):
            logger.warning(
                f"Access denied: User '{request.user.username}' "
                f"(ID: {request.user.id}) attempted to access '{url_name}' "
                f"from IP {self._get_client_ip(request)}"
            )
            return redirect('no_permission')

        return None

    def _has_access(self, user, url_name):
        """
        Check if user has access to URL with caching.
        """
        if not url_name:
            return True

        # Check cache first
        cache_key = f"rbac:user:{user.id}:url:{url_name}"
        has_access = cache.get(cache_key)

        if has_access is not None:
            return has_access

        # Cache miss - query database
        try:
            user_groups = user.groups.values_list('id', flat=True)
            has_access = RoleURLAccess.objects.filter(
                role_id__in=user_groups,
                url_name=url_name
            ).exists()

            # Cache result for 5 minutes
            cache.set(cache_key, has_access, 300)

            return has_access

        except Exception as e:
            logger.error(f"RBAC database error: {e}", exc_info=True)
            # Fail open (allow access) or fail closed (deny access)?
            # For security, fail closed:
            return False

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### 2.4 Custom Managers for Queries

```python
# siswa/managers.py
from django.db import models
from django.db.models import Q, Count, Avg
from django.utils import timezone

class SiswaQuerySet(models.QuerySet):
    """Custom QuerySet for Siswa model"""

    def active(self):
        """Return only active students"""
        return self.filter(status='aktif')

    def by_kelompok(self, kelompok):
        """Filter by kelompok"""
        return self.filter(kelompok=kelompok)

    def by_jenjang(self, jenjang):
        """Filter by jenjang (through kelompok)"""
        return self.filter(kelompok__jenjang=jenjang)

    def with_full_details(self):
        """Optimize query with all related data"""
        return self.select_related(
            'kelompok',
            'kelompok__jenjang',
            'periode'
        ).prefetch_related(
            'kehadiran_set',
            'kateringentry_set'
        )

    def with_attendance_stats(self):
        """Annotate with attendance statistics"""
        return self.annotate(
            total_kehadiran=Count('kehadiran'),
            hadir_count=Count('kehadiran', filter=Q(kehadiran__kehadiran='hadir')),
        )

    def search(self, query):
        """Search by NIS or name"""
        return self.filter(
            Q(nis__icontains=query) |
            Q(nama__icontains=query)
        )

    def graduated_in_period(self, periode):
        """Get students who graduated in specific period"""
        return self.filter(status='lulus', periode=periode)


class SiswaManager(models.Manager):
    """Custom Manager for Siswa model"""

    def get_queryset(self):
        return SiswaQuerySet(self.model, using=self._db)

    # Proxy methods for convenience
    def active(self):
        return self.get_queryset().active()

    def by_kelompok(self, kelompok):
        return self.get_queryset().by_kelompok(kelompok)

    def with_full_details(self):
        return self.get_queryset().with_full_details()

    def search(self, query):
        return self.get_queryset().search(query)


# Usage in model
class Siswa(models.Model):
    # ... fields ...

    objects = SiswaManager()

    class Meta:
        db_table = 'siswa'


# Usage in views
class SiswaListView(ListView):
    def get_queryset(self):
        queryset = Siswa.objects.active().with_full_details()

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.search(search)

        return queryset
```

---

## Phase 3: Database Optimization

### 3.1 Add Indexes

```python
# siswa/models.py
class Siswa(models.Model):
    nis = models.CharField(max_length=20, unique=True, db_index=True)
    nama = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif', db_index=True)

    class Meta:
        db_table = 'siswa'
        indexes = [
            models.Index(fields=['nis']),
            models.Index(fields=['nama']),
            models.Index(fields=['status']),
            models.Index(fields=['kelompok', 'status']),  # Composite index
            models.Index(fields=['-created_at']),  # Descending index
        ]

# Generate migration
# python manage.py makemigrations
# python manage.py migrate
```

### 3.2 Database Connection Pooling

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling: reuse connections for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 seconds
        },
    }
}
```

### 3.3 Query Optimization

```python
# ❌ BAD: N+1 Query Problem
def bad_list_view(request):
    students = Siswa.objects.all()
    for student in students:
        print(student.kelompok.nama)  # N queries!
        print(student.kehadiran_set.count())  # N more queries!

# ✅ GOOD: Optimized with select_related and prefetch_related
def good_list_view(request):
    students = Siswa.objects.select_related(
        'kelompok',
        'kelompok__jenjang'
    ).prefetch_related(
        'kehadiran_set'
    ).annotate(
        kehadiran_count=Count('kehadiran')
    )

    for student in students:
        print(student.kelompok.nama)  # No extra query
        print(student.kehadiran_count)  # No extra query

# ✅ BETTER: Use only() or defer() for large models
def optimized_list_view(request):
    # Only fetch needed fields
    students = Siswa.objects.only(
        'id', 'nis', 'nama', 'kelompok__nama'
    ).select_related('kelompok')

    # Or defer large fields
    students = Siswa.objects.defer('alamat').select_related('kelompok')
```

### 3.4 Add Timestamps

```python
# core/models.py
from django.db import models

class TimeStampedModel(models.Model):
    """
    Abstract base class with created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Usage
class Siswa(TimeStampedModel):
    # ... other fields ...
    pass

# Now all models have created_at and updated_at
# Generate migration to add these fields to existing tables
```

---

## Phase 4: Error Handling & Logging

### 4.1 Configure Logging

```python
# settings.py
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'siswa': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'pegawai': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'keuangan': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory
import os
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
```

### 4.2 Usage in Views

```python
# siswa/views.py
import logging

logger = logging.getLogger(__name__)

class SiswaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Siswa
    form_class = SiswaForm

    def form_valid(self, form):
        try:
            response = super().form_valid(form)

            logger.info(
                f"New student created: {self.object.nis} - {self.object.nama} "
                f"by user {self.request.user.username}"
            )

            return response

        except Exception as e:
            logger.error(
                f"Error creating student: {e}",
                exc_info=True,
                extra={
                    'user': self.request.user.username,
                    'form_data': form.cleaned_data,
                }
            )
            messages.error(self.request, 'Terjadi kesalahan saat menyimpan data.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(
            f"Invalid form submission for student creation "
            f"by user {self.request.user.username}. "
            f"Errors: {form.errors}"
        )
        return super().form_invalid(form)
```

### 4.3 Custom Error Pages

```python
# core/views.py
from django.shortcuts import render

def handler404(request, exception):
    """Custom 404 error page"""
    logger = logging.getLogger(__name__)
    logger.warning(f"404 error: {request.path} by {request.user}")

    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error page"""
    logger = logging.getLogger(__name__)
    logger.error(f"500 error: {request.path} by {request.user}")

    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    """Custom 403 error page"""
    return render(request, 'errors/403.html', status=403)

# urls.py
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
handler403 = 'core.views.handler403'
```

```django
<!-- templates/errors/404.html -->
{% extends "backend/base.html" %}
{% block content %}
<div class="error-page">
    <h2 class="headline text-warning"> 404</h2>
    <div class="error-content">
        <h3><i class="fas fa-exclamation-triangle text-warning"></i> Oops! Halaman tidak ditemukan.</h3>
        <p>
            Halaman yang Anda cari tidak dapat ditemukan.
            Silakan kembali ke <a href="{% url 'dashboard' %}">dashboard</a>
            atau gunakan menu navigasi.
        </p>
    </div>
</div>
{% endblock %}
```

### 4.4 Error Tracking with Sentry

```bash
pip install sentry-sdk
```

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
        environment='production',
    )
```

---

## Phase 5: Service Layer Pattern

### 5.1 Create Service Layer

```python
# siswa/services.py
from typing import List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Siswa, Kehadiran
import logging

logger = logging.getLogger(__name__)

class SiswaService:
    """
    Service layer for Siswa business logic.
    Separates business logic from views.
    """

    @staticmethod
    def get_active_students(kelompok=None, jenjang=None):
        """
        Get active students with optional filtering.

        Args:
            kelompok: Kelompok instance (optional)
            jenjang: Jenjang code (optional)

        Returns:
            QuerySet of active students
        """
        queryset = Siswa.objects.active().with_full_details()

        if kelompok:
            queryset = queryset.by_kelompok(kelompok)

        if jenjang:
            queryset = queryset.by_jenjang(jenjang)

        return queryset

    @staticmethod
    @transaction.atomic
    def create_student(data: dict, created_by) -> Siswa:
        """
        Create new student with validation and audit trail.

        Args:
            data: Dictionary of student data
            created_by: User creating the student

        Returns:
            Created Siswa instance

        Raises:
            ValidationError: If data is invalid
        """
        # Business validation
        if Siswa.objects.filter(nis=data.get('nis')).exists():
            raise ValidationError({'nis': 'NIS sudah terdaftar'})

        # Create student
        siswa = Siswa.objects.create(**data)

        # Log activity
        logger.info(
            f"Student created: {siswa.nis} - {siswa.nama} "
            f"by {created_by.username}"
        )

        # You can add more business logic here:
        # - Send notification
        # - Create default settings
        # - Generate QR code
        # etc.

        return siswa

    @staticmethod
    @transaction.atomic
    def update_student(siswa: Siswa, data: dict, updated_by) -> Siswa:
        """Update student data"""
        # Check if NIS changed and is duplicate
        if data.get('nis') != siswa.nis:
            if Siswa.objects.filter(nis=data.get('nis')).exists():
                raise ValidationError({'nis': 'NIS sudah terdaftar'})

        # Update fields
        for field, value in data.items():
            setattr(siswa, field, value)

        siswa.save()

        logger.info(
            f"Student updated: {siswa.nis} - {siswa.nama} "
            f"by {updated_by.username}"
        )

        return siswa

    @staticmethod
    @transaction.atomic
    def delete_student(siswa: Siswa, deleted_by) -> None:
        """
        Delete student (or soft delete).
        Also deletes related data as needed.
        """
        nis = siswa.nis
        nama = siswa.nama

        # Delete or soft delete
        siswa.delete()

        logger.info(
            f"Student deleted: {nis} - {nama} "
            f"by {deleted_by.username}"
        )

    @staticmethod
    def calculate_attendance_percentage(siswa: Siswa, periode=None) -> float:
        """
        Calculate attendance percentage for student.

        Args:
            siswa: Siswa instance
            periode: Optional Periode instance

        Returns:
            Attendance percentage (0-100)
        """
        kehadiran_qs = Kehadiran.objects.filter(siswa=siswa)

        if periode:
            # Filter by period dates
            kehadiran_qs = kehadiran_qs.filter(
                tanggal__gte=periode.tanggal_mulai,
                tanggal__lte=periode.tanggal_selesai
            )

        total = kehadiran_qs.count()
        if total == 0:
            return 0.0

        hadir = kehadiran_qs.filter(kehadiran='hadir').count()

        return (hadir / total) * 100

    @staticmethod
    def get_student_report(siswa: Siswa) -> dict:
        """
        Generate comprehensive report for student.

        Returns:
            Dictionary with report data
        """
        from django.db.models import Count, Q

        # Attendance stats
        kehadiran_stats = Kehadiran.objects.filter(siswa=siswa).aggregate(
            total=Count('id'),
            hadir=Count('id', filter=Q(kehadiran='hadir')),
            sakit=Count('id', filter=Q(kehadiran='sakit')),
            izin=Count('id', filter=Q(kehadiran='izin')),
            tidak_hadir=Count('id', filter=Q(kehadiran='tidak_hadir')),
        )

        # Calculate percentage
        total = kehadiran_stats['total']
        percentage = (kehadiran_stats['hadir'] / total * 100) if total > 0 else 0

        return {
            'siswa': siswa,
            'kehadiran': kehadiran_stats,
            'persentase_kehadiran': percentage,
            # Add more data as needed
        }


# Usage in views
class SiswaCreateView(CreateView):
    def form_valid(self, form):
        try:
            siswa = SiswaService.create_student(
                data=form.cleaned_data,
                created_by=self.request.user
            )
            messages.success(self.request, f'Siswa {siswa.nama} berhasil ditambahkan')
            return redirect('siswa:list')

        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
```

### 5.2 Transaction Management

```python
# Example: Complex transaction with rollback
from django.db import transaction

class PegawaiService:
    @staticmethod
    @transaction.atomic
    def process_monthly_salary(periode_bulan, periode_tahun):
        """
        Process salary for all employees for a given month.
        Uses transaction to ensure all-or-nothing execution.
        """
        try:
            pegawai_list = Pegawai.objects.filter(status='active')

            for pegawai in pegawai_list:
                # Calculate salary components
                gaji_pokok = pegawai.gaji_pokok or 0

                # Get attendance bonus
                absen = AbsenPegawai.objects.filter(
                    pegawai=pegawai,
                    tanggal__month=periode_bulan,
                    tanggal__year=periode_tahun
                ).aggregate(
                    total_insentif=Sum('insentif')
                )
                bonus_insentif = absen['total_insentif'] or 0

                # Get loan deduction
                pinjaman_aktif = PinjamanPegawai.objects.filter(
                    pegawai=pegawai,
                    tanggal_pelunasan__isnull=True
                ).first()

                potongan_pinjaman = pinjaman_aktif.angsuran_per_bulan if pinjaman_aktif else 0

                # Create salary record
                gaji = GajiPegawai.objects.create(
                    pegawai=pegawai,
                    periode_bulan=periode_bulan,
                    periode_tahun=periode_tahun,
                    gaji_pokok=gaji_pokok,
                    bonus_insentif=bonus_insentif,
                    pinjaman=potongan_pinjaman,
                    # ... other fields
                )

                # Update loan
                if pinjaman_aktif:
                    pinjaman_aktif.sudah_terbayar += potongan_pinjaman
                    if pinjaman_aktif.sisa_pinjaman <= 0:
                        pinjaman_aktif.tanggal_pelunasan = timezone.now().date()
                    pinjaman_aktif.save()

            logger.info(f"Salary processed for {pegawai_list.count()} employees")
            return True

        except Exception as e:
            logger.error(f"Error processing salary: {e}", exc_info=True)
            # Transaction will be rolled back automatically
            raise
```

---

## Best Practices

### 1. Code Organization

```
beesmartfinance/
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── services.py      # ✅ Business logic
│   ├── managers.py      # ✅ Custom managers
│   ├── mixins.py        # ✅ Reusable mixins
│   ├── validators.py    # ✅ Custom validators
│   ├── utils.py         # ✅ Utility functions
│   └── tests/           # ✅ Tests
│       ├── test_models.py
│       ├── test_views.py
│       └── test_services.py
```

### 2. Naming Conventions

```python
# Models: Singular, PascalCase
class Siswa(models.Model):
    pass

# Views: PascalCase + ViewType suffix
class SiswaListView(ListView):
    pass

# Services: PascalCase + Service suffix
class SiswaService:
    pass

# Functions: snake_case
def calculate_attendance_percentage(siswa):
    pass

# Constants: UPPERCASE
MAX_UPLOAD_SIZE = 5242880  # 5MB
STATUS_ACTIVE = 'aktif'
```

### 3. Documentation

```python
def calculate_monthly_salary(pegawai: Pegawai, month: int, year: int) -> Decimal:
    """
    Calculate monthly salary for employee including bonuses and deductions.

    Args:
        pegawai (Pegawai): Employee instance
        month (int): Month number (1-12)
        year (int): Year (e.g., 2024)

    Returns:
        Decimal: Total salary amount

    Raises:
        ValidationError: If month or year is invalid

    Example:
        >>> pegawai = Pegawai.objects.get(nik='123456')
        >>> salary = calculate_monthly_salary(pegawai, 1, 2024)
        >>> print(salary)
        Decimal('5000000.00')
    """
    pass
```

### 4. Type Hints

```python
from typing import List, Optional, Dict, Any
from django.db.models import QuerySet

def get_students_by_kelompok(kelompok_id: int) -> QuerySet[Siswa]:
    """Get students by kelompok ID"""
    return Siswa.objects.filter(kelompok_id=kelompok_id)

def create_student_dict(siswa: Siswa) -> Dict[str, Any]:
    """Convert student to dictionary"""
    return {
        'nis': siswa.nis,
        'nama': siswa.nama,
        'kelompok': siswa.kelompok.nama if siswa.kelompok else None,
    }
```

### 5. Error Handling

```python
# ❌ BAD
def get_siswa(nis):
    siswa = Siswa.objects.get(nis=nis)  # May raise DoesNotExist!
    return siswa

# ✅ GOOD
from django.shortcuts import get_object_or_404

def get_siswa_safe(nis):
    """Get student or return 404"""
    return get_object_or_404(Siswa, nis=nis)

# ✅ BETTER with logging
def get_siswa_with_logging(nis):
    """Get student with error logging"""
    try:
        return Siswa.objects.get(nis=nis)
    except Siswa.DoesNotExist:
        logger.warning(f"Student not found: NIS={nis}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting student: {e}", exc_info=True)
        raise
```

### 6. Testing

```python
# siswa/tests/test_services.py
from django.test import TestCase
from siswa.models import Siswa, Kelompok, Jenjang
from siswa.services import SiswaService

class SiswaServiceTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.jenjang = Jenjang.objects.create(kode='TK', nama='TK')
        self.kelompok = Kelompok.objects.create(
            jenjang=self.jenjang,
            nama='A'
        )

    def test_create_student(self):
        """Test creating student via service"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create(username='test')

        data = {
            'nis': '001',
            'nama': 'Test Student',
            'kelompok': self.kelompok,
            'spp': 500000,
        }

        siswa = SiswaService.create_student(data, created_by=user)

        self.assertEqual(siswa.nis, '001')
        self.assertEqual(siswa.nama, 'Test Student')
        self.assertEqual(Siswa.objects.count(), 1)

    def test_duplicate_nis_raises_error(self):
        """Test that duplicate NIS raises ValidationError"""
        # ... test implementation
```

---

## Summary

Dengan mengikuti panduan ini, backend akan:

✅ **Lebih aman** - Security hardening, proper secrets management
✅ **Lebih maintainable** - Class-based views, service layer pattern
✅ **Lebih performant** - Database optimization, caching, query optimization
✅ **Lebih robust** - Proper error handling, logging, monitoring
✅ **Lebih testable** - Separation of concerns, dependency injection

**Next Steps**:
1. Review [API Development Guide](./03-API-DEVELOPMENT.md)
2. Review [Testing Guide](./05-TESTING-GUIDE.md)
3. Start implementing phase by phase

---

**Last Updated**: 2025-12-28
**Version**: 1.0.0
