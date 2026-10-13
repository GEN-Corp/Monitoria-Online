from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Ticket, TicketMessage
from .querysets import tickets_for_user
from .serializers import TicketSerializer, TicketMessageSerializer


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return tickets_for_user(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        user = self.request.user

        if user.tipo != "ALUNO" and not user.is_superuser:
            raise PermissionDenied(
                "Somente alunos podem abrir tickets."
            )

        serializer.save(student=user)


class TicketMessageViewSet(viewsets.ModelViewSet):
    serializer_class = TicketMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TicketMessage.objects.filter(
            ticket__in=tickets_for_user(self.request.user)
        ).order_by("created_at")

    def perform_create(self, serializer):
        user = self.request.user
        ticket = serializer.validated_data["ticket"]

        if not tickets_for_user(user).filter(pk=ticket.pk).exists():
            raise PermissionDenied(
                "Você não tem acesso a este ticket."
            )

        if ticket.status in ("RESOLVED", "CLOSED"):
            raise PermissionDenied(
                "Não é possível responder a um ticket encerrado."
            )

        message = serializer.save(author=user)
        if user.is_superuser or user.tipo in ("MONITOR", "PROFESSOR", "COORDENADOR"):
            message.ticket.status = Ticket.Status.ANSWERED
        else:
            message.ticket.status = Ticket.Status.IN_PROGRESS
        message.ticket.save(update_fields=["status", "updated_at"])