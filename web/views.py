from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from users.models import User
from courses.models import Course
from monitoring.models import Monitoring
from tickets.models import Ticket, TicketMessage
from tickets.querysets import tickets_for_user
from .forms import CourseForm, MonitoringAssignmentForm


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
            tipo=User.TipoUsuario.ALUNO,
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

    courses = Course.objects.filter(
        active=True,
        monitorings__status="ACTIVE",
    ).distinct()

    if request.method == "POST":
        course_id = request.POST.get("course")
        subject = request.POST.get("subject")
        description = request.POST.get("description")

        course = get_object_or_404(
            Course,
            id=course_id,
            active=True,
            monitorings__status="ACTIVE",
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
        if not request.user.is_superuser:
            return redirect("dashboard")

    tickets = tickets_for_user(request.user).order_by("-created_at")

    return render(
        request,
        "web/monitor_tickets.html",
        {"tickets": tickets},
    )

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        tickets_for_user(request.user).select_related(
            "student", "course", "monitoring"
        ).prefetch_related("messages__author"),
        pk=ticket_id,
    )

    error = None
    can_reply = ticket.status not in (
        Ticket.Status.RESOLVED,
        Ticket.Status.CLOSED,
    )

    if request.method == "POST":
        message_text = request.POST.get("message", "").strip()
        if not can_reply:
            error = "Esta dúvida já foi encerrada."
        elif not message_text:
            error = "Escreva uma mensagem antes de enviar."
        else:
            TicketMessage.objects.create(
                ticket=ticket,
                author=request.user,
                message=message_text,
            )
            if (
                request.user.is_superuser
                or request.user.tipo in ("MONITOR", "PROFESSOR", "COORDENADOR")
            ):
                ticket.status = Ticket.Status.ANSWERED
            else:
                ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save(update_fields=["status", "updated_at"])
            return redirect("ticket_detail", ticket_id=ticket.id)

    return render(
        request,
        "web/ticket_detail.html",
        {"ticket": ticket, "can_reply": can_reply, "error": error},
    )


def professor_managed_courses(user):
    return Course.objects.filter(
        Q(created_by=user) | Q(monitorings__professor=user)
    ).distinct()


@login_required
def professor_courses(request):
    if request.user.tipo != User.TipoUsuario.PROFESSOR:
        raise PermissionDenied

    courses = professor_managed_courses(request.user).prefetch_related(
        "monitorings__monitor"
    )
    return render(
        request,
        "web/professor_courses.html",
        {"courses": courses},
    )


@login_required
def professor_course_create(request):
    if request.user.tipo != User.TipoUsuario.PROFESSOR:
        raise PermissionDenied

    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        course = form.save(commit=False)
        course.created_by = request.user
        course.save()
        return redirect("professor_course_assignments", course_id=course.pk)

    return render(request, "web/course_form.html", {"form": form})


@login_required
def professor_course_assignments(request, course_id):
    if request.user.tipo != User.TipoUsuario.PROFESSOR:
        raise PermissionDenied

    course = get_object_or_404(
        professor_managed_courses(request.user),
        pk=course_id,
    )
    form = MonitoringAssignmentForm(
        request.POST or None,
        course=course,
    )

    if request.method == "POST" and form.is_valid():
        monitor = form.cleaned_data["monitor"]
        assignment, created = Monitoring.objects.get_or_create(
            course=course,
            monitor=monitor,
            professor=request.user,
            defaults={
                "status": Monitoring.Status.ACTIVE,
                "start_date": timezone.localdate(),
            },
        )
        if not created and assignment.status != Monitoring.Status.ACTIVE:
            assignment.status = Monitoring.Status.ACTIVE
            assignment.start_date = timezone.localdate()
            assignment.end_date = None
            assignment.save(
                update_fields=["status", "start_date", "end_date"]
            )
        return redirect("professor_course_assignments", course_id=course.pk)

    assignments = Monitoring.objects.filter(
        course=course,
        professor=request.user,
    ).select_related("monitor")
    return render(
        request,
        "web/course_assignments.html",
        {
            "course": course,
            "form": form,
            "assignments": assignments,
        },
    )