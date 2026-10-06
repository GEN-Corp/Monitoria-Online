from rest_framework import serializers

from firebase_backend.records import MessageRecord, TicketRecord


class TicketMessageSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    ticket = serializers.CharField(source="ticket_id", read_only=True)
    author = serializers.CharField(source="author.uid", read_only=True)
    author_name = serializers.CharField(source="author.username", read_only=True)
    message = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = MessageRecord


class TicketMessageCreateSerializer(serializers.Serializer):
    ticket = serializers.CharField()
    message = serializers.CharField()


class TicketSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    student = serializers.CharField(source="student.uid", read_only=True)
    student_name = serializers.CharField(source="student.username", read_only=True)
    course = serializers.CharField(source="course.id", read_only=True)
    course_id = serializers.CharField(write_only=True)
    monitoring = serializers.CharField(read_only=True, allow_null=True)
    subject = serializers.CharField(max_length=200)
    description = serializers.CharField()
    status = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = TicketRecord

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["status"] = instance.status
        data["priority"] = instance.priority
        data["monitoring"] = None
        return data
