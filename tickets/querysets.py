from django.db.models import F, Q

from .models import Ticket


def tickets_for_user(user):
    if user.is_superuser or user.tipo == "COORDENADOR":
        return Ticket.objects.all()

    if user.tipo == "ALUNO":
        return Ticket.objects.filter(student=user)

    if user.tipo == "MONITOR":
        return Ticket.objects.filter(
            Q(
                monitoring__monitor=user,
                monitoring__course=F("course"),
                monitoring__status="ACTIVE",
            )
            | Q(
                course__monitorings__monitor=user,
                course__monitorings__status="ACTIVE",
            )
        ).distinct()

    if user.tipo == "PROFESSOR":
        return Ticket.objects.filter(
            Q(
                monitoring__professor=user,
                monitoring__course=F("course"),
                monitoring__status="ACTIVE",
            )
            | Q(
                course__monitorings__professor=user,
                course__monitorings__status="ACTIVE",
            )
        ).distinct()

    return Ticket.objects.none()
