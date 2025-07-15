from django.db import models
from django.contrib.auth.models import Group

class RoleURLAccess(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    url_pattern = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.group.name} can access {self.url_pattern}"
