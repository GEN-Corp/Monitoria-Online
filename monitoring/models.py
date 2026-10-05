from django.conf import settings
from django.db import models

from courses.models import Course


class Monitoring(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        INACTIVE = "INACTIVE", "Inativa"

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="monitorings",
    )

    monitor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="monitorings",
    )

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="professor_monitorings",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} - Monitor: {self.monitor.username}"