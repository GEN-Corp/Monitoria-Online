from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"