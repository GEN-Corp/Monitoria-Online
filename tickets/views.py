from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Ticket, TicketMessage
from .serializers import TicketSerializer, TicketMessageSerializer


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser or user.tipo == "COORDENADOR":
            return Ticket.objects.all().order_by("-created_at")

        if user.tipo == "ALUNO":
            return Ticket.objects.filter(
                student=user
            ).order_by("-created_at")

        if user.tipo == "MONITOR":
            return Ticket.objects.filter(
                monitoring__monitor=user
            ).order_by("-created_at")

        if user.tipo == "PROFESSOR":
            return Ticket.objects.filter(
                monitoring__professor=user
            ).order_by("-created_at")

        return Ticket.objects.none()

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
        visible_tickets = TicketViewSet(
            request=self.request
        ).get_queryset()

        return TicketMessage.objects.filter(
            ticket__in=visible_tickets
        ).order_by("created_at")

    def perform_create(self, serializer):
        user = self.request.user
        ticket = serializer.validated_data["ticket"]

        if not TicketViewSet(
            request=self.request
        ).get_queryset().filter(pk=ticket.pk).exists():
            raise PermissionDenied(
                "Você não tem acesso a este ticket."
            )

        if ticket.status in ("RESOLVED", "CLOSED"):
            raise PermissionDenied(
                "Não é possível responder a um ticket encerrado."
            )

        serializer.save(author=user)