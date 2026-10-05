from django.contrib import admin

from .models import Ticket, TicketMessage


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "course",
        "subject",
        "status",
        "priority",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "course",
    )

    search_fields = (
        "subject",
        "description",
        "student__username",
    )


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ticket",
        "author",
        "created_at",
    )

    search_fields = (
        "message",
        "author__username",
    )