# 🧪 Testing Strategy Guide

## Setup

```bash
pip install pytest pytest-django pytest-cov factory-boy faker
```

## Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = penelitian_tk.settings
python_files = tests.py test_*.py *_tests.py
```

## Test Structure

```
siswa/
├── tests/
│   ├── __init__.py
│   ├── factories.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_api.py
│   └── test_services.py
```

## Factory Pattern

```python
# siswa/tests/factories.py
import factory
from faker import Faker
from siswa.models import Siswa, Kelompok, Jenjang

fake = Faker('id_ID')

class JenjangFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Jenjang
    
    kode = 'TK'
    nama = 'Taman Kanak-kanak'

class KelompokFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Kelompok
    
    jenjang = factory.SubFactory(JenjangFactory)
    nama = factory.Faker('random_element', elements=['A', 'B', 'C'])

class SiswaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Siswa
    
    nis = factory.Sequence(lambda n: f'{n:05d}')
    nama = factory.Faker('name', locale='id_ID')
    kelompok = factory.SubFactory(KelompokFactory)
    spp = 500000
    status = 'aktif'
```

## Model Tests

```python
# siswa/tests/test_models.py
import pytest
from siswa.tests.factories import SiswaFactory

@pytest.mark.django_db
class TestSiswaModel:
    def test_create_siswa(self):
        siswa = SiswaFactory()
        assert siswa.id is not None
        assert siswa.status == 'aktif'
    
    def test_nis_unique(self):
        SiswaFactory(nis='001')
        with pytest.raises(Exception):
            SiswaFactory(nis='001')
```

## API Tests

```python
# siswa/tests/test_api.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from siswa.tests.factories import SiswaFactory

@pytest.mark.django_db
class TestSiswaAPI:
    def setup_method(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='test',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_siswa(self):
        SiswaFactory.create_batch(5)
        response = self.client.get('/api/siswa/')
        assert response.status_code == 200
        assert len(response.data['results']) == 5
    
    def test_create_siswa(self):
        data = {
            'nis': '001',
            'nama': 'Test Student',
            'spp': 500000,
        }
        response = self.client.post('/api/siswa/', data)
        assert response.status_code == 201
```

## Coverage Target

```bash
# Run tests with coverage
pytest --cov=siswa --cov-report=html

# Target: 60%+ backend, 70%+ frontend
```

