# 📝 Code Style & Conventions Guide

## Python Style (PEP 8)

### Naming Conventions
```python
# Classes: PascalCase
class StudentService:
    pass

# Functions/Methods: snake_case
def calculate_attendance_percentage():
    pass

# Constants: UPPERCASE
MAX_UPLOAD_SIZE = 5242880

# Variables: snake_case
student_list = []

# Private: _leading_underscore
def _internal_helper():
    pass
```

### Imports
```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party
from django.db import models
from rest_framework import serializers

# Local
from .models import Siswa
from .services import SiswaService
```

### Docstrings
```python
def calculate_salary(employee, month, year):
    """
    Calculate monthly salary for employee.

    Args:
        employee (Pegawai): Employee instance
        month (int): Month number (1-12)
        year (int): Year (e.g., 2024)

    Returns:
        Decimal: Total salary amount

    Raises:
        ValidationError: If month or year is invalid
    """
    pass
```

## JavaScript/Vue Style

### Component Naming
```vue
<!-- PascalCase for components -->
<script>
export default {
  name: 'StudentList'
}
</script>
```

### Variable Naming
```javascript
// camelCase
const studentList = []
const isActive = true

// UPPERCASE for constants
const MAX_FILE_SIZE = 5242880
```

### Vue Composition API
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'

// Reactive state
const students = ref([])
const loading = ref(false)

// Computed
const activeStudents = computed(() => 
  students.value.filter(s => s.status === 'aktif')
)

// Methods
function fetchStudents() {
  // ...
}

// Lifecycle
onMounted(() => {
  fetchStudents()
})
</script>
```

## Git Conventions

### Branch Naming
```bash
feature/student-crud
bugfix/attendance-calculation
hotfix/security-issue
refactor/service-layer
```

### Commit Messages
```bash
# Format: <type>: <subject>

feat: Add student CRUD API endpoints
fix: Fix attendance calculation bug
refactor: Migrate views to CBV
docs: Update API documentation
test: Add tests for SiswaService
style: Format code with black
chore: Update dependencies
```

## Code Quality Tools

```bash
# Black (formatter)
pip install black
black .

# Flake8 (linter)
pip install flake8
flake8 .

# isort (import sorting)
pip install isort
isort .

# mypy (type checking)
pip install mypy
mypy .
```

