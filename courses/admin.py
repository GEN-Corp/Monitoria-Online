from django.contrib import admin

from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "active", "created_by")
    list_filter = ("active",)
    search_fields = ("code", "name", "created_by__username")