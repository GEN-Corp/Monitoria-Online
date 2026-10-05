from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    dashboard,
    register,
    ticket_create,
    ticket_list,
    monitor_tickets,
    ticket_detail,
)


urlpatterns = [
    path("", dashboard, name="dashboard"),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="web/login.html"
        ),
        name="login",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path(
        "cadastro/",
        register,
        name="register",
    ),

    path(
        "tickets/",
        ticket_list,
        name="ticket_list",
    ),

    path(
        "tickets/novo/",
        ticket_create,
        name="ticket_create",
    ),

    path(
    "atendimentos/",
    monitor_tickets,
    name="monitor_tickets",
    ),

    path(
    "tickets/<int:ticket_id>/",
    ticket_detail,
    name="ticket_detail",
    ),
]