from django.db import models
from django.conf import settings


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_courses",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.code} - {self.name}"