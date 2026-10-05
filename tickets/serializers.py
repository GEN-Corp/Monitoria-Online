from rest_framework import serializers

from .models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    class Meta:
        model = TicketMessage
        fields = [
            "id",
            "ticket",
            "author",
            "author_name",
            "message",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "author",
            "created_at",
        ]


class TicketSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.username",
        read_only=True,
    )

    messages = TicketMessageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "monitoring",
            "subject",
            "description",
            "status",
            "priority",
            "created_at",
            "updated_at",
            "messages",
        ]

        read_only_fields = [
            "id",
            "student",
            "created_at",
            "updated_at",
            "messages",
        ]