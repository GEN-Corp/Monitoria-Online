from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class TipoUsuario(models.TextChoices):
        ALUNO = "ALUNO", "Aluno"
        MONITOR = "MONITOR", "Monitor"
        PROFESSOR = "PROFESSOR", "Professor"
        COORDENADOR = "COORDENADOR", "Coordenador"

    tipo = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.ALUNO,
    )

    def __str__(self):
        return f"{self.username} - {self.get_tipo_display()}"