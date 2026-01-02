# 🔒 Security Best Practices Guide

## Critical Security Checklist

### 1. Environment & Configuration
- [ ] `DEBUG = False` in production
- [ ] Secret key from environment variable (no fallback)
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] Database credentials in environment variables
- [ ] `.env` file in `.gitignore`

### 2. HTTPS & Headers
```python
# Production settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 3. Password Security
```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### 4. Rate Limiting
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    pass
```

### 5. Input Validation
```python
# Always validate user input
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Invalid phone number"
)
```

### 6. SQL Injection Prevention
```python
# ✅ SAFE - Use ORM
Siswa.objects.filter(nis=user_input)

# ❌ UNSAFE - Raw SQL
query = f"SELECT * FROM siswa WHERE nis = '{user_input}'"
```

### 7. XSS Prevention
```django
{# ✅ Auto-escaped #}
{{ user_input }}

{# ⚠️ Use carefully #}
{{ html_content|safe }}
```

### 8. CSRF Protection
```django
{% csrf_token %}
```

### 9. Audit Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"User {user.username} accessed {resource}")
logger.warning(f"Failed login attempt from {ip_address}")
logger.error(f"Error processing payment: {error}")
```

### 10. Error Handling
- Custom 404/500 error pages
- No sensitive information in error messages
- Sentry for error tracking in production

