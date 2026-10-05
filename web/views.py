from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from users.models import User
from courses.models import Course
from tickets.models import Ticket


@login_required
def dashboard(request):
    return render(request, "web/dashboard.html")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        tipo = request.POST.get("tipo")

        if password != password_confirm:
            return render(
                request,
                "web/register.html",
                {"error": "As senhas não coincidem."},
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "web/register.html",
                {"error": "Esse usuário já existe."},
            )

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            tipo=tipo,
        )

        login(request, user)

        return redirect("dashboard")

    return render(request, "web/register.html")


@login_required
def ticket_list(request):
    tickets = Ticket.objects.filter(
        student=request.user
    ).order_by("-created_at")

    return render(
        request,
        "web/tickets.html",
        {"tickets": tickets},
    )


@login_required
def ticket_create(request):
    if request.user.tipo != "ALUNO":
        return redirect("dashboard")

    courses = Course.objects.filter(active=True)

    if request.method == "POST":
        course_id = request.POST.get("course")
        subject = request.POST.get("subject")
        description = request.POST.get("description")

        course = get_object_or_404(
            Course,
            id=course_id,
            active=True,
        )

        Ticket.objects.create(
            student=request.user,
            course=course,
            subject=subject,
            description=description,
        )

        return redirect("ticket_list")

    return render(
        request,
        "web/ticket_form.html",
        {"courses": courses},
    )

@login_required
def monitor_tickets(request):
    if request.user.tipo not in ["MONITOR", "PROFESSOR", "COORDENADOR"]:
        return redirect("dashboard")

    if request.user.tipo == "MONITOR":
        tickets = Ticket.objects.filter(
            monitoring__monitor=request.user
        ).order_by("-created_at")

    elif request.user.tipo == "PROFESSOR":
        tickets = Ticket.objects.filter(
            monitoring__professor=request.user
        ).order_by("-created_at")

    else:
        tickets = Ticket.objects.all().order_by("-created_at")

    return render(
        request,
        "web/monitor_tickets.html",
        {"tickets": tickets},
    )

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        Ticket,
        id=ticket_id,
    )

    if request.user.tipo == "ALUNO":
        if ticket.student != request.user:
            return redirect("ticket_list")

    elif request.user.tipo == "MONITOR":
        if ticket.monitoring and ticket.monitoring.monitor != request.user:
            return redirect("dashboard")

    elif request.user.tipo == "PROFESSOR":
        if ticket.monitoring and ticket.monitoring.professor != request.user:
            return redirect("dashboard")

    return render(
        request,
        "web/ticket_detail.html",
        {"ticket": ticket},
    )