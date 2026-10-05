from django.conf import settings
from django.db import models

from courses.models import Course
from monitoring.models import Monitoring


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        IN_PROGRESS = "IN_PROGRESS", "Em atendimento"
        RESOLVED = "RESOLVED", "Resolvido"
        CLOSED = "CLOSED", "Fechado"

    class Priority(models.TextChoices):
        LOW = "LOW", "Baixa"
        MEDIUM = "MEDIUM", "Média"
        HIGH = "HIGH", "Alta"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="tickets",
    )

    monitoring = models.ForeignKey(
        Monitoring,
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
    )

    subject = models.CharField(max_length=200)
    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} - {self.subject}"


# COLOCA A SEGUNDA PARTE AQUI 👇

class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ticket_messages",
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Mensagem #{self.id} - Ticket #{self.ticket.id}"