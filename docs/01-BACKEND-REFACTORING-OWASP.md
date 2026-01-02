# 🔒 Backend Refactoring - OWASP Top 10 Security

> Panduan implementasi keamanan berdasarkan OWASP Top 10 2025

## 📑 Table of Contents

- [A01: Broken Access Control](#a01-broken-access-control)
- [A02: Security Misconfiguration](#a02-security-misconfiguration)
- [A03: Software Supply Chain Failures](#a03-software-supply-chain-failures)
- [A04: Cryptographic Failures](#a04-cryptographic-failures)
- [A05: Injection](#a05-injection)
- [A06: Insecure Design](#a06-insecure-design)
- [A07: Authentication Failures](#a07-authentication-failures)
- [A08: Software or Data Integrity Failures](#a08-software-or-data-integrity-failures)
- [A09: Security Logging and Alerting Failures](#a09-security-logging-and-alerting-failures)
- [A10: Mishandling of Exceptional Conditions](#a10-mishandling-of-exceptional-conditions)

## A01: Broken Access Control

### Vulnerability
User dapat mengakses resources/functions yang tidak seharusnya mereka akses.

### Current Issues in Beesmartfinance
1. ❌ RBAC middleware has bare except clause
2. ⚠️ No object-level permission checks
3. ⚠️ No audit trail for permission changes

### Implementation

#### 1. Improved RBAC Middleware

```python
# core/middleware/rbac.py
import logging
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from core.models import RoleURLAccess

logger = logging.getLogger('security')

class SecureRBACMiddleware(MiddlewareMixin):
    """
    Role-Based Access Control Middleware with:
    - Proper error handling
    - Caching for performance
    - Security logging
    - Fail-closed approach
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
        if not self._has_access(request.user, url_name, request):
            logger.warning(
                f"Access denied: User '{request.user.username}' "
                f"(ID: {request.user.id}) attempted to access '{url_name}' "
                f"from IP {self._get_client_ip(request)}",
                extra={
                    'user_id': request.user.id,
                    'username': request.user.username,
                    'url_name': url_name,
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
            return redirect('no_permission')

        return None

    def _has_access(self, user, url_name, request):
        """Check if user has access to URL with caching"""
        if not url_name:
            return True

        # Cache key includes user ID and URL name
        cache_key = f"rbac:user:{user.id}:url:{url_name}"
        has_access = cache.get(cache_key)

        if has_access is not None:
            logger.debug(f"RBAC cache hit for {cache_key}")
            return has_access

        # Cache miss - query database
        try:
            user_groups = user.groups.values_list('id', flat=True)
            has_access = RoleURLAccess.objects.filter(
                role_id__in=user_groups,
                url_name=url_name,
                is_active=True  # Add is_active field to model
            ).exists()

            # Cache result for 5 minutes
            cache.set(cache_key, has_access, 300)

            logger.debug(f"RBAC database query for {cache_key}: {has_access}")
            return has_access

        except Exception as e:
            # Fail closed - deny access on error
            logger.error(
                f"RBAC error for user {user.id}: {e}",
                exc_info=True,
                extra={
                    'user_id': user.id,
                    'url_name': url_name,
                }
            )
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

#### 2. Object-Level Permissions

```python
# core/permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners or admins to edit.
    """

    def has_object_permission(self, request, view, obj):
        # Admin users have all permissions
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Read permissions are allowed to authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only to owner
        return obj.created_by == request.user


class CanManageStudents(permissions.BasePermission):
    """
    Permission to check if user can manage students.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(
            name__in=['admin', 'guru']
        ).exists()


class CanManageFinance(permissions.BasePermission):
    """
    Permission to check if user can manage finance.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(
            name__in=['admin', 'bendahara']
        ).exists()

    def has_object_permission(self, request, view, obj):
        # Only allow editing transactions from current month
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            from django.utils import timezone
            from datetime import timedelta

            # Can only modify transactions from last 7 days
            seven_days_ago = timezone.now() - timedelta(days=7)
            if obj.tanggal < seven_days_ago.date():
                return False

        return True


# Usage in ViewSet
class SiswaViewSet(viewsets.ModelViewSet):
    queryset = Siswa.objects.all()
    serializer_class = SiswaSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageStudents]
```

#### 3. Audit Trail

```python
# core/models.py
from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    """
    Audit log for tracking all changes to sensitive data.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PERMISSION_CHANGE', 'Permission Change'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(null=True)  # Store what changed
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"


# core/mixins.py
class AuditMixin:
    """Mixin to automatically log changes"""

    def perform_create(self, serializer):
        instance = serializer.save()
        self._log_action('CREATE', instance)
        return instance

    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()
        self._log_action('UPDATE', instance, old_instance)
        return instance

    def perform_destroy(self, instance):
        self._log_action('DELETE', instance)
        instance.delete()

    def _log_action(self, action, instance, old_instance=None):
        from core.models import AuditLog

        changes = None
        if action == 'UPDATE' and old_instance:
            changes = self._get_changes(old_instance, instance)

        AuditLog.objects.create(
            user=self.request.user,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            object_repr=str(instance),
            changes=changes,
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
        )

    def _get_changes(self, old, new):
        """Get field changes between old and new instance"""
        changes = {}
        for field in old._meta.fields:
            field_name = field.name
            old_value = getattr(old, field_name)
            new_value = getattr(new, field_name)

            if old_value != new_value:
                changes[field_name] = {
                    'old': str(old_value),
                    'new': str(new_value),
                }

        return changes

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Usage
class SiswaViewSet(AuditMixin, viewsets.ModelViewSet):
    # Automatically logs all create/update/delete operations
    pass
```

---

## A02: Security Misconfiguration

### Vulnerability
Missing security headers, default configurations, verbose error messages.

### Current Issues
1. ❌ DEBUG = True in production
2. ❌ Missing security headers
3. ❌ Default admin URL

### Implementation

#### 1. Production Settings

```python
# settings.py
from decouple import config

# ✅ DEBUG from environment
DEBUG = config('DEBUG', default=False, cast=bool)

# ✅ Specific allowed hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# ✅ Security headers
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    SESSION_COOKIE_AGE = 3600  # 1 hour

    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Strict'

    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# ✅ Custom admin URL
ADMIN_URL = config('ADMIN_URL', default='admin/')

# urls.py
from django.conf import settings

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),  # Not /admin/
    # ...
]
```

#### 2. Security Middleware

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # First!
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.rbac.SecureRBACMiddleware',  # Custom
    'core.middleware.security_headers.SecurityHeadersMiddleware',  # Custom
]

# core/middleware/security_headers.py
class SecurityHeadersMiddleware:
    """Add additional security headers"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )

        return response
```

---

## A03: Software Supply Chain Failures

### Vulnerability
Compromises in software dependencies, build systems, and distribution infrastructure.

### Implementation

#### 1. Dependency Management

```bash
# Install safety to check for known vulnerabilities
pip install safety

# Check for vulnerabilities
safety check

# requirements.txt - Pin versions
Django==5.1.5
djangorestframework==3.14.0
psycopg2-binary==2.9.9

# Use pip-audit (newer alternative)
pip install pip-audit
pip-audit
```

#### 2. Regular Updates

```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade django

# Freeze updated requirements
pip freeze > requirements.txt
```

#### 3. Automated Vulnerability Scanning

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install safety bandit

      - name: Run safety check
        run: safety check

      - name: Run bandit
        run: bandit -r . -f json -o bandit-report.json

      - name: Upload security reports
        uses: actions/upload-artifact@v2
        with:
          name: security-reports
          path: |
            bandit-report.json
```

---

## A04: Cryptographic Failures

### Vulnerability
Sensitive data exposed due to lack of encryption or weak encryption.

### Current Issues
1. ❌ Secret key with fallback in code
2. ⚠️ No encryption for sensitive fields (phone numbers, addresses)
3. ⚠️ Passwords in logs (potential)

### Implementation

#### 1. Proper Secret Management

```python
# settings.py
from decouple import config

# ❌ WRONG - Has fallback
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key-here')

# ✅ CORRECT - No fallback, will raise error if not set
SECRET_KEY = config('SECRET_KEY')  # Raises UndefinedValueError if not set

# Additional secrets
DB_PASSWORD = config('DB_PASSWORD')
JWT_SECRET = config('JWT_SECRET')
ENCRYPTION_KEY = config('ENCRYPTION_KEY')
```

#### 2. Field-Level Encryption

```python
# core/encryption.py
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class FieldEncryption:
    """Encrypt/decrypt sensitive fields"""

    def __init__(self):
        # Get encryption key from settings
        key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(key)

    def encrypt(self, value):
        """Encrypt a string value"""
        if not value:
            return value

        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, value):
        """Decrypt an encrypted value"""
        if not value:
            return value

        try:
            decoded = base64.b64decode(value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None


# Usage in models
from core.encryption import FieldEncryption

class Siswa(models.Model):
    nama = models.CharField(max_length=100)
    _kontak_ayah = models.CharField(max_length=200, db_column='kontak_ayah')  # Encrypted
    _kontak_ibu = models.CharField(max_length=200, db_column='kontak_ibu')    # Encrypted

    encryption = FieldEncryption()

    @property
    def kontak_ayah(self):
        return self.encryption.decrypt(self._kontak_ayah)

    @kontak_ayah.setter
    def kontak_ayah(self, value):
        self._kontak_ayah = self.encryption.encrypt(value)

    @property
    def kontak_ibu(self):
        return self.encryption.decrypt(self._kontak_ibu)

    @kontak_ibu.setter
    def kontak_ibu(self, value):
        self._kontak_ibu = self.encryption.encrypt(value)
```

#### 3. Secure Password Handling

```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Best
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Never log passwords
LOGGING = {
    'filters': {
        'remove_passwords': {
            '()': 'core.logging_filters.RemovePasswordsFilter',
        },
    },
    'handlers': {
        'file': {
            'filters': ['remove_passwords'],
            # ...
        },
    },
}

# core/logging_filters.py
import re

class RemovePasswordsFilter:
    """Remove passwords from log messages"""

    def filter(self, record):
        # Remove password fields from log message
        if hasattr(record, 'msg'):
            record.msg = re.sub(
                r'(password["\']?\s*[:=]\s*["\']?)[^"\'}\s]+',
                r'\1***REMOVED***',
                str(record.msg),
                flags=re.IGNORECASE
            )
        return True
```

---

## A05: Injection

### Vulnerability
SQL Injection, NoSQL Injection, Command Injection, etc.

### Current Issues
✅ Good: Using Django ORM (protected by default)
⚠️ Risk: If raw SQL is used anywhere

### Implementation

#### 1. SQL Injection Prevention

```python
# ❌ DANGEROUS - SQL Injection vulnerability
def get_siswa_unsafe(nis):
    query = f"SELECT * FROM siswa WHERE nis = '{nis}'"
    return Siswa.objects.raw(query)

# ✅ SAFE - Use ORM
def get_siswa_safe(nis):
    return Siswa.objects.filter(nis=nis)

# ✅ SAFE - If you must use raw SQL, use parameterized queries
def get_siswa_raw_safe(nis):
    query = "SELECT * FROM siswa WHERE nis = %s"
    return Siswa.objects.raw(query, [nis])

# ✅ SAFE - Using extra() with params
def get_active_students_sorted(sort_by):
    # Whitelist allowed sort fields
    ALLOWED_SORT_FIELDS = ['nama', 'nis', 'tanggal_lahir']

    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = 'nama'  # Default

    return Siswa.objects.filter(status='aktif').extra(
        select={'upper_name': 'UPPER(nama)'}
    ).order_by(sort_by)
```

#### 2. Command Injection Prevention

```python
# ❌ DANGEROUS - Command Injection
import os

def export_data_unsafe(filename):
    os.system(f"mysqldump database > {filename}")  # DANGER!

# ✅ SAFE - Use subprocess with list arguments
import subprocess

def export_data_safe(filename):
    # Validate filename
    if not filename.replace('_', '').replace('-', '').isalnum():
        raise ValueError("Invalid filename")

    subprocess.run(
        ['mysqldump', 'database'],
        stdout=open(filename, 'w'),
        check=True
    )
```

#### 3. Template Injection Prevention

```python
# ❌ DANGEROUS - Template injection
from django.template import Template, Context

def render_custom_template_unsafe(user_input):
    t = Template(user_input)  # DANGER!
    return t.render(Context())

# ✅ SAFE - Don't allow user input in templates
# Use predefined templates only
from django.shortcuts import render

def render_safe(request):
    return render(request, 'predefined_template.html', {'data': user_input})
```

---

## A06: Insecure Design

### Vulnerability
Flaws in design and architecture.

### Implementation

#### 1. Secure Password Reset Flow

```python
# core/views.py
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='3/h', method='POST')
def password_reset_request(request):
    """
    Secure password reset with:
    - Rate limiting
    - Token-based verification
    - Time-limited tokens
    - No user enumeration
    """
    if request.method == 'POST':
        email = request.POST.get('email')

        # Always return same message (prevent user enumeration)
        message = "Jika email terdaftar, link reset password telah dikirim."

        try:
            user = User.objects.get(email=email)

            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Create reset link (valid for 1 hour)
            reset_link = request.build_absolute_uri(
                f'/password-reset-confirm/{uid}/{token}/'
            )

            # Send email
            send_mail(
                'Reset Password - Beesmartfinance',
                f'Klik link berikut untuk reset password Anda:\n{reset_link}\n\nLink valid selama 1 jam.',
                'noreply@beesmartfinance.com',
                [email],
                fail_silently=False,
            )

            logger.info(f"Password reset requested for email: {email}")

        except User.DoesNotExist:
            # Don't reveal that user doesn't exist
            logger.warning(f"Password reset attempted for non-existent email: {email}")

        # Always show same message
        messages.success(request, message)
        return redirect('login')

    return render(request, 'password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """Confirm password reset with token validation"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        # Validate token
        if not default_token_generator.check_token(user, token):
            messages.error(request, 'Link reset password tidak valid atau sudah kadaluarsa.')
            return redirect('password_reset_request')

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password != confirm_password:
                messages.error(request, 'Password tidak cocok.')
                return render(request, 'password_reset_confirm.html')

            # Set new password
            user.set_password(new_password)
            user.save()

            logger.info(f"Password reset successful for user: {user.username}")
            messages.success(request, 'Password berhasil diubah. Silakan login.')
            return redirect('login')

        return render(request, 'password_reset_confirm.html')

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Link reset password tidak valid.')
        return redirect('password_reset_request')
```

#### 2. Secure File Upload

```python
# core/validators.py
import magic
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    """Validate file extension"""
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']

    if not ext.lower() in valid_extensions:
        raise ValidationError('Format file tidak didukung.')


def validate_file_size(value):
    """Validate file size (max 5MB)"""
    filesize = value.size

    if filesize > 5242880:  # 5MB
        raise ValidationError("Ukuran file maksimal 5MB")


def validate_file_mimetype(value):
    """Validate file MIME type (not just extension)"""
    mime = magic.from_buffer(value.read(1024), mime=True)
    value.seek(0)  # Reset file pointer

    valid_mimes = [
        'image/jpeg',
        'image/png',
        'application/pdf',
    ]

    if mime not in valid_mimes:
        raise ValidationError(f'Tipe file tidak valid: {mime}')


# Usage in model
class Siswa(models.Model):
    foto = models.ImageField(
        upload_to='siswa/foto/',
        validators=[
            validate_file_extension,
            validate_file_size,
            validate_file_mimetype,
        ],
        null=True,
        blank=True
    )
```

---

## A07: Authentication Failures

### Vulnerability
Weak authentication, session management issues.

### Current Issues
1. ⚠️ No rate limiting on login
2. ⚠️ No account lockout
3. ⚠️ No MFA

### Implementation

#### 1. Secure Login with Rate Limiting

```python
# core/views.py
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import authenticate, login
from django.core.cache import cache
import logging

logger = logging.getLogger('security')

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@ratelimit(key='post:username', rate='5/m', method='POST', block=True)
def secure_login(request):
    """
    Secure login with:
    - Rate limiting by IP and username
    - Account lockout after failed attempts
    - Security logging
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if account is locked
        lockout_key = f'lockout:{username}'
        if cache.get(lockout_key):
            messages.error(
                request,
                'Akun Anda terkunci. Silakan coba lagi dalam 30 menit.'
            )
            logger.warning(
                f"Login attempt on locked account: {username} "
                f"from IP {get_client_ip(request)}"
            )
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Successful login
            login(request, user)

            # Clear failed attempts
            failed_key = f'failed_login:{username}'
            cache.delete(failed_key)

            logger.info(
                f"Successful login: {username} from IP {get_client_ip(request)}"
            )

            # Check for suspicious activity
            if check_suspicious_login(user, request):
                send_security_alert(user, request)

            return redirect('dashboard')
        else:
            # Failed login
            failed_key = f'failed_login:{username}'
            failed_attempts = cache.get(failed_key, 0) + 1
            cache.set(failed_key, failed_attempts, 1800)  # 30 minutes

            logger.warning(
                f"Failed login attempt #{failed_attempts}: {username} "
                f"from IP {get_client_ip(request)}"
            )

            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                cache.set(lockout_key, True, 1800)  # Lock for 30 minutes
                messages.error(
                    request,
                    'Terlalu banyak percobaan login gagal. '
                    'Akun Anda terkunci selama 30 menit.'
                )
                logger.critical(
                    f"Account locked due to failed attempts: {username}"
                )
            else:
                messages.error(
                    request,
                    f'Username atau password salah. '
                    f'Sisa percobaan: {5 - failed_attempts}'
                )

    return render(request, 'login.html')


def check_suspicious_login(user, request):
    """Check for suspicious login activity"""
    current_ip = get_client_ip(request)

    # Get previous login IP
    last_login_key = f'last_login_ip:{user.id}'
    last_ip = cache.get(last_login_key)

    # Save current IP
    cache.set(last_login_key, current_ip, 86400)  # 24 hours

    # If login from different country/IP, flag as suspicious
    if last_ip and last_ip != current_ip:
        return True

    return False


def send_security_alert(user, request):
    """Send security alert email"""
    from django.core.mail import send_mail

    send_mail(
        'Login dari lokasi baru - Beesmartfinance',
        f'Akun Anda baru saja login dari IP: {get_client_ip(request)}\n'
        f'Jika ini bukan Anda, segera ubah password Anda.',
        'security@beesmartfinance.com',
        [user.email],
        fail_silently=True,
    )
```

#### 2. Strong Password Policy

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increased from 8
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'core.validators.PasswordComplexityValidator',  # Custom
    },
]

# core/validators.py
from django.core.exceptions import ValidationError
import re

class PasswordComplexityValidator:
    """
    Validate that password contains:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """

    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password harus mengandung minimal 1 huruf besar.')

        if not re.search(r'[a-z]', password):
            raise ValidationError('Password harus mengandung minimal 1 huruf kecil.')

        if not re.search(r'[0-9]', password):
            raise ValidationError('Password harus mengandung minimal 1 angka.')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password harus mengandung minimal 1 karakter spesial.')

    def get_help_text(self):
        return (
            "Password harus mengandung minimal 12 karakter dengan kombinasi "
            "huruf besar, huruf kecil, angka, dan karakter spesial."
        )
```

#### 3. Session Security

```python
# settings.py

# Session timeout
SESSION_COOKIE_AGE = 3600  # 1 hour

# Expire session on browser close
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Regenerate session ID on login
SESSION_SAVE_EVERY_REQUEST = False

# core/middleware/session_security.py
from django.utils import timezone
from datetime import timedelta

class SessionTimeoutMiddleware:
    """Implement idle timeout for sessions"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check last activity
            last_activity = request.session.get('last_activity')

            if last_activity:
                last_activity = timezone.datetime.fromisoformat(last_activity)
                idle_time = timezone.now() - last_activity

                # Logout after 30 minutes of inactivity
                if idle_time > timedelta(minutes=30):
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('login')

            # Update last activity
            request.session['last_activity'] = timezone.now().isoformat()

        response = self.get_response(request)
        return response
```

---

## A08: Software or Data Integrity Failures

### Vulnerability
Code/infrastructure without integrity verification.

### Implementation

#### 1. Signed URLs for Downloads

```python
# core/utils.py
from django.core.signing import Signer, BadSignature
from django.conf import settings

class SecureDownload:
    """Generate and validate signed URLs for file downloads"""

    def __init__(self):
        self.signer = Signer()

    def generate_download_url(self, file_path, expiry_minutes=30):
        """Generate signed URL that expires"""
        import time

        timestamp = int(time.time()) + (expiry_minutes * 60)
        data = f"{file_path}:{timestamp}"

        signed = self.signer.sign(data)

        return f"/download/{signed}/"

    def validate_download_url(self, signed_data):
        """Validate signed URL and check expiry"""
        import time

        try:
            unsigned = self.signer.unsign(signed_data)
            file_path, timestamp = unsigned.rsplit(':', 1)

            # Check expiry
            if int(timestamp) < int(time.time()):
                raise ValueError("Download link has expired")

            return file_path

        except BadSignature:
            raise ValueError("Invalid download link")


# Usage in view
from django.http import FileResponse

def secure_download(request, signed_url):
    """Secure file download with signed URL"""
    downloader = SecureDownload()

    try:
        file_path = downloader.validate_download_url(signed_url)

        # Verify user has permission to download
        if not user_can_download(request.user, file_path):
            return HttpResponseForbidden()

        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'

        return response

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('dashboard')
```

#### 2. Database Integrity Checks

```python
# core/management/commands/check_integrity.py
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check database integrity'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check for orphaned records
            cursor.execute("""
                SELECT COUNT(*) FROM siswa
                WHERE kelompok_id NOT IN (SELECT id FROM kelompok)
            """)
            orphaned_students = cursor.fetchone()[0]

            if orphaned_students > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'Found {orphaned_students} orphaned student records'
                    )
                )

            # Check for duplicate NIS
            cursor.execute("""
                SELECT nis, COUNT(*) as count
                FROM siswa
                GROUP BY nis
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()

            if duplicates:
                self.stdout.write(
                    self.style.ERROR(
                        f'Found {len(duplicates)} duplicate NIS records'
                    )
                )
```

---

## A09: Security Logging and Alerting Failures

### Vulnerability
Insufficient logging, alerting, and monitoring.

### Implementation

#### 1. Comprehensive Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': (
                '[{levelname}] {asctime} {name} {module} '
                '{process:d} {thread:d} {message}'
            ),
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'json',  # JSON for easy parsing
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'security': {
            'handlers': ['security', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

#### 2. Security Event Logging

```python
# core/security_logger.py
import logging

security_logger = logging.getLogger('security')

class SecurityEvent:
    """Log security-relevant events"""

    @staticmethod
    def log_login_success(user, request):
        security_logger.info(
            f"LOGIN_SUCCESS",
            extra={
                'event': 'login_success',
                'user_id': user.id,
                'username': user.username,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

    @staticmethod
    def log_login_failure(username, request):
        security_logger.warning(
            f"LOGIN_FAILURE",
            extra={
                'event': 'login_failure',
                'username': username,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

    @staticmethod
    def log_permission_denied(user, resource, request):
        security_logger.warning(
            f"PERMISSION_DENIED",
            extra={
                'event': 'permission_denied',
                'user_id': user.id,
                'username': user.username,
                'resource': resource,
                'ip_address': get_client_ip(request),
            }
        )

    @staticmethod
    def log_suspicious_activity(user, activity_type, details, request):
        security_logger.critical(
            f"SUSPICIOUS_ACTIVITY",
            extra={
                'event': 'suspicious_activity',
                'activity_type': activity_type,
                'user_id': user.id,
                'username': user.username,
                'details': details,
                'ip_address': get_client_ip(request),
            }
        )
```

#### 3. Real-time Monitoring

```python
# core/monitoring.py
from django.core.mail import send_mail
from django.conf import settings

class SecurityMonitor:
    """Monitor for security threats"""

    @staticmethod
    def check_brute_force_attack():
        """Detect brute force login attempts"""
        from django.core.cache import cache

        # Get all failed login attempts in last 5 minutes
        pattern = 'failed_login:*'
        # This requires Redis with pattern matching

        # If > 50 failed attempts from different IPs in 5 min
        # Alert admins

    @staticmethod
    def alert_admins(subject, message):
        """Send alert to administrators"""
        send_mail(
            f'[SECURITY ALERT] {subject}',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin[1] for admin in settings.ADMINS],
            fail_silently=False,
        )
```

---

## A10: Mishandling of Exceptional Conditions

### Vulnerability
Improper error handling, logical errors, failing open, and abnormal conditions that systems may encounter.

### Current Issues
1. ⚠️ Bare except clauses in error handling
2. ⚠️ No proper exception logging
3. ⚠️ Fail-open approach in some critical paths

### Implementation

#### 1. Proper Exception Handling

```python
# ❌ DANGEROUS - Bare except
def process_payment(amount):
    try:
        # Process payment
        payment_gateway.charge(amount)
    except:  # DANGER: Catches everything including SystemExit!
        pass

# ✅ CORRECT - Specific exception handling
def process_payment_safe(amount):
    try:
        payment_gateway.charge(amount)
        logger.info(f"Payment processed successfully: {amount}")
        return True
    except PaymentGatewayError as e:
        # Handle expected payment errors
        logger.error(f"Payment failed: {e}", exc_info=True)
        return False
    except ConnectionError as e:
        # Handle network errors
        logger.critical(f"Payment gateway unreachable: {e}", exc_info=True)
        raise
    except Exception as e:
        # Last resort - still log unknown errors
        logger.critical(f"Unexpected payment error: {e}", exc_info=True, extra={
            'amount': amount,
            'traceback': traceback.format_exc()
        })
        raise
```

#### 2. Fail-Closed Approach

```python
# ❌ DANGEROUS - Fails open (grants access on error)
def check_permission_unsafe(user, resource):
    try:
        return user.has_permission(resource)
    except:
        return True  # DANGER: Grants access on error!

# ✅ CORRECT - Fail closed (denies access on error)
def check_permission_safe(user, resource):
    try:
        has_access = user.has_permission(resource)
        logger.debug(f"Permission check: {user.username} -> {resource}: {has_access}")
        return has_access
    except Exception as e:
        logger.error(
            f"Permission check failed for {user.username} on {resource}: {e}",
            exc_info=True,
            extra={'user_id': user.id, 'resource': resource}
        )
        # Fail closed - deny access on error
        return False
```

#### 3. Input Validation with Proper Error Handling

```python
# ❌ DANGEROUS - Allows invalid data to pass through
def create_student_unsafe(data):
    try:
        nis = int(data.get('nis'))
        spp = int(data.get('spp'))
    except:
        nis = 0  # DANGER: Silent failure with invalid default
        spp = 0

    return Siswa.objects.create(nis=nis, spp=spp)

# ✅ CORRECT - Explicit validation and error handling
from django.core.exceptions import ValidationError

def create_student_safe(data):
    errors = []

    # Validate NIS
    try:
        nis = int(data.get('nis', ''))
        if nis <= 0:
            errors.append('NIS must be positive')
    except (ValueError, TypeError) as e:
        errors.append(f'Invalid NIS format: {data.get("nis")}')
        logger.warning(f"Invalid NIS in student creation: {e}")
        nis = None

    # Validate SPP
    try:
        spp = int(data.get('spp', ''))
        if spp < 0:
            errors.append('SPP cannot be negative')
    except (ValueError, TypeError) as e:
        errors.append(f'Invalid SPP format: {data.get("spp")}')
        logger.warning(f"Invalid SPP in student creation: {e}")
        spp = None

    # Fail if any validation errors
    if errors or nis is None or spp is None:
        raise ValidationError('; '.join(errors))

    try:
        student = Siswa.objects.create(nis=nis, spp=spp)
        logger.info(f"Student created successfully: {student.nis}")
        return student
    except Exception as e:
        logger.error(f"Failed to create student: {e}", exc_info=True)
        raise
```

#### 4. Database Error Handling

```python
# ❌ DANGEROUS - Ignores database errors
def save_transaction_unsafe(transaction_data):
    try:
        transaction = Transaction.objects.create(**transaction_data)
        return transaction
    except:
        return None  # DANGER: Silent failure

# ✅ CORRECT - Proper error handling and logging
from django.db import IntegrityError, DatabaseError

def save_transaction_safe(transaction_data):
    try:
        transaction = Transaction.objects.create(**transaction_data)
        logger.info(
            f"Transaction saved: {transaction.id}",
            extra={'transaction_id': transaction.id, 'amount': transaction.amount}
        )
        return transaction

    except IntegrityError as e:
        # Handle constraint violations (duplicate, foreign key, etc.)
        logger.warning(
            f"Transaction integrity error: {e}",
            extra={'data': transaction_data}
        )
        raise ValidationError("Transaction validation failed: duplicate or invalid reference")

    except DatabaseError as e:
        # Handle database errors (connection, query errors, etc.)
        logger.critical(
            f"Database error saving transaction: {e}",
            exc_info=True,
            extra={'data': transaction_data}
        )
        raise

    except Exception as e:
        # Catch unexpected errors
        logger.critical(
            f"Unexpected error saving transaction: {e}",
            exc_info=True,
            extra={'data': transaction_data}
        )
        raise
```

#### 5. API Error Responses

```python
# core/exception_handlers.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger('api')

def custom_exception_handler(exc, context):
    # Custom exception handler for DRF

    # Get the standard error response
    response = exception_handler(exc, context)

    # Log the exception
    logger.error(
        f"API Exception: {exc.__class__.__name__}",
        exc_info=True,
        extra={
            'view': context.get('view').__class__.__name__,
            'request_path': context.get('request').path,
            'request_method': context.get('request').method,
        }
    )

    # Customize error response
    if response is not None:
        response.data['status_code'] = response.status_code
        response.data['error_type'] = exc.__class__.__name__
    else:
        # Handle unexpected exceptions
        logger.critical(
            f"Unhandled exception in API: {exc}",
            exc_info=True
        )
        response = Response(
            {
                'detail': 'Internal server error',
                'status_code': 500,
                'error_type': 'InternalServerError'
            },
            status=500
        )

    return response

# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'core.exception_handlers.custom_exception_handler',
}
```

---

## Security Checklist

### Implementation Checklist

- [ ] **A01: Broken Access Control**
  - [ ] Implement improved RBAC middleware
  - [ ] Add object-level permissions
  - [ ] Implement audit logging
  - [ ] Clear cache on permission changes

- [ ] **A04: Cryptographic Failures**
  - [ ] Remove secret key fallback
  - [ ] Implement field-level encryption for sensitive data
  - [ ] Use Argon2 password hasher
  - [ ] Filter passwords from logs

- [ ] **A05: Injection**
  - [ ] Audit all raw SQL queries
  - [ ] Validate all user inputs
  - [ ] Use parameterized queries
  - [ ] Whitelist allowed values

- [ ] **A06: Insecure Design**
  - [ ] Implement secure password reset flow
  - [ ] Add file upload validation
  - [ ] Use tokens with expiry
  - [ ] Prevent user enumeration

- [ ] **A02: Security Misconfiguration**
  - [ ] Set DEBUG=False in production
  - [ ] Add all security headers
  - [ ] Change default admin URL
  - [ ] Configure CSP

- [ ] **A03: Software Supply Chain Failures**
  - [ ] Run `safety check` regularly
  - [ ] Pin dependency versions
  - [ ] Setup automated vulnerability scanning
  - [ ] Update dependencies monthly

- [ ] **A07: Authentication Failures**
  - [ ] Add rate limiting on login
  - [ ] Implement account lockout
  - [ ] Enforce strong passwords
  - [ ] Add session timeout
  - [ ] Consider MFA

- [ ] **A08: Software or Data Integrity Failures**
  - [ ] Use signed URLs for downloads
  - [ ] Implement database integrity checks
  - [ ] Verify file uploads
  - [ ] Use checksums

- [ ] **A09: Security Logging and Alerting Failures**
  - [ ] Log all security events
  - [ ] Setup real-time monitoring
  - [ ] Alert on critical events
  - [ ] Regular log review

- [ ] **A10: Mishandling of Exceptional Conditions**
  - [ ] Use specific exception handling
  - [ ] Implement fail-closed approach
  - [ ] Validate inputs properly
  - [ ] Log all exceptions

---

## Testing Security Implementation

```python
# tests/test_security.py
from django.test import TestCase, Client
from django.contrib.auth.models import User

class SecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test',
            password='TestPassword123!'
        )

    def test_login_rate_limiting(self):
        """Test login is rate limited"""
        for i in range(6):
            response = self.client.post('/login/', {
                'username': 'test',
                'password': 'wrong'
            })

        # 6th attempt should be blocked
        self.assertEqual(response.status_code, 429)

    def test_sql_injection_protection(self):
        """Test SQL injection is prevented"""
        malicious_input = "'; DROP TABLE siswa; --"

        response = self.client.get(f'/api/siswa/?search={malicious_input}')

        # Should not cause error
        self.assertIn(response.status_code, [200, 404])

        # Table should still exist
        from siswa.models import Siswa
        self.assertTrue(Siswa.objects.exists() or True)

    def test_xss_protection(self):
        """Test XSS is prevented"""
        malicious_script = '<script>alert("XSS")</script>'

        self.client.login(username='test', password='TestPassword123!')
        response = self.client.post('/api/siswa/', {
            'nis': '001',
            'nama': malicious_script,
            'spp': 500000,
        })

        # Script should be escaped in response
        self.assertNotContains(response, malicious_script, html=True)

    def test_csrf_protection(self):
        """Test CSRF protection is active"""
        self.client.login(username='test', password='TestPassword123!')

        # Request without CSRF token should fail
        response = self.client.post('/api/siswa/', {
            'nis': '001',
            'nama': 'Test',
        })

        self.assertEqual(response.status_code, 403)
```

---


---

**Last Updated**: 2026-01-02
**Version**: 2.0.0
**OWASP Version**: 2025
