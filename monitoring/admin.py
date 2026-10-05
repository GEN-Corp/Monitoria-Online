from django.contrib import admin

from .models import Monitoring


@admin.register(Monitoring)
class MonitoringAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "monitor",
        "professor",
        "status",
        "start_date",
        "end_date",
    )

    list_filter = ("status", "course")

    search_fields = (
        "course__name",
        "course__code",
        "monitor__username",
        "professor__username",
    )