from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied as APIPermissionDenied
from rest_framework.exceptions import ValidationError as APIValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from firebase_backend.repository import (
    add_message,
    create_ticket,
    get_ticket_for_user,
    list_messages,
    list_tickets,
)
from .serializers import (
    TicketMessageCreateSerializer,
    TicketMessageSerializer,
    TicketSerializer,
)


class TicketViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        tickets = list_tickets(request.user, include_messages=True)
        return Response(TicketSerializer(tickets, many=True).data)

    def retrieve(self, request, pk=None):
        ticket = get_ticket_for_user(pk, request.user)
        if ticket is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(TicketSerializer(ticket).data)

    def create(self, request):
        if request.user.tipo != "ALUNO":
            raise APIPermissionDenied("Somente alunos podem abrir dúvidas.")
        serializer = TicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ticket = create_ticket(
                request.user,
                serializer.validated_data["course_id"],
                serializer.validated_data["subject"],
                serializer.validated_data["description"],
            )
        except ValidationError as exception:
            raise APIValidationError(exception.messages) from exception
        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
        )


class TicketMessageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        messages = [
            message
            for ticket in list_tickets(request.user, include_messages=True)
            for message in ticket.messages
        ]
        messages.sort(key=lambda message: message.created_at)
        return Response(TicketMessageSerializer(messages, many=True).data)

    def retrieve(self, request, pk=None):
        for ticket in list_tickets(request.user, include_messages=True):
            for message in ticket.messages:
                if message.id == pk:
                    return Response(TicketMessageSerializer(message).data)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = TicketMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            add_message(
                request.user,
                serializer.validated_data["ticket"],
                serializer.validated_data["message"],
            )
        except PermissionDenied as exception:
            raise APIPermissionDenied(str(exception)) from exception
        except ValidationError as exception:
            raise APIValidationError(exception.messages) from exception
        message = list_messages(serializer.validated_data["ticket"])[-1]
        return Response(
            TicketMessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )
