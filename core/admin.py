from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin

# (Opsional) unregister kalau sudah terdaftar sebelumnya
admin.site.unregister(User)
admin.site.unregister(Group)

# Register ulang agar bisa dimodifikasi
admin.site.register(User, UserAdmin)
admin.site.register(Group)
