from django.urls import path

from .views import (
    dashboard,
    firebase_login,
    firebase_logout,
    register,
    ticket_create,
    ticket_list,
    monitor_tickets,
    ticket_detail,
    professor_courses,
    professor_course_create,
    professor_course_assignments,
)


urlpatterns = [
    path("", dashboard, name="dashboard"),

    path(
        "login/",
        firebase_login,
        name="login",
    ),

    path(
        "logout/",
        firebase_logout,
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
    "tickets/<str:ticket_id>/",
    ticket_detail,
    name="ticket_detail",
    ),
    path(
        "professor/disciplinas/",
        professor_courses,
        name="professor_courses",
    ),
    path(
        "professor/disciplinas/nova/",
        professor_course_create,
        name="professor_course_create",
    ),
    path(
        "professor/disciplinas/<str:course_id>/monitores/",
        professor_course_assignments,
        name="professor_course_assignments",
    ),
]