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

    def validate(self, attrs):
        course = attrs.get("course", getattr(self.instance, "course", None))
        monitoring = attrs.get(
            "monitoring",
            getattr(self.instance, "monitoring", None),
        )

        if course is None or not course.active:
            raise serializers.ValidationError(
                {"course": "Selecione uma disciplina ativa."}
            )

        if not course.monitorings.filter(status="ACTIVE").exists():
            raise serializers.ValidationError(
                {"course": "A disciplina não possui monitoria ativa."}
            )

        if monitoring and (
            monitoring.course_id != course.pk
            or monitoring.status != "ACTIVE"
        ):
            raise serializers.ValidationError(
                {"monitoring": "A monitoria precisa ser ativa e pertencer à disciplina."}
            )

        return attrs