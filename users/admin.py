from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Informações da Monitoria", {
            "fields": ("tipo",),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Informações da Monitoria", {
            "fields": ("tipo",),
        }),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "tipo",
        "is_active",
    )

    list_filter = ("tipo", "is_active")