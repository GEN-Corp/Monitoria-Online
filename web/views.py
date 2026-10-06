import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from firebase_admin import auth

from firebase_backend.identity import (
    FirebaseIdentityError,
    SESSION_COOKIE_NAME,
    SESSION_DURATION,
    create_session_cookie,
    create_user,
    sign_in,
)
from firebase_backend.repository import (
    add_message,
    assign_monitor,
    create_course,
    create_ticket,
    ensure_student_profile,
    get_course,
    get_user,
    get_ticket_for_user,
    list_active_courses_for_students,
    list_monitors,
    list_professor_courses,
    list_tickets,
)
from .forms import CourseForm, MonitoringAssignmentForm, RegistrationForm


logger = logging.getLogger(__name__)


def _set_firebase_cookie(response, id_token):
    cookie = create_session_cookie(id_token)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        cookie,
        max_age=int(SESSION_DURATION.total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/",
    )
    return response


def firebase_login(request):
    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        try:
            token_response = sign_in(email, password)
            claims = auth.verify_id_token(token_response["idToken"])
            if get_user(claims["uid"]) is None:
                ensure_student_profile(claims["uid"], email)
            response = redirect("dashboard")
            return _set_firebase_cookie(response, token_response["idToken"])
        except (
            FirebaseIdentityError,
            auth.InvalidIdTokenError,
            ImproperlyConfigured,
        ) as exception:
            error = str(exception) or "E-mail ou senha inválidos."
        except KeyError:
            logger.exception("Firebase sign-in response did not contain an ID token.")
            error = "O Firebase retornou uma resposta de login inválida."

    return render(request, "web/login.html", {"error": error})


def register(request):
    form = RegistrationForm(request.POST or None)
    error = None
    if request.method == "POST" and form.is_valid():
        try:
            token_response = create_user(
                form.cleaned_data["email"].strip().lower(),
                form.cleaned_data["password"],
            )
            claims = auth.verify_id_token(token_response["idToken"])
            ensure_student_profile(
                claims["uid"],
                form.cleaned_data["email"].strip().lower(),
                form.cleaned_data["first_name"].strip(),
                form.cleaned_data["last_name"].strip(),
            )
            response = redirect("dashboard")
            return _set_firebase_cookie(response, token_response["idToken"])
        except (
            FirebaseIdentityError,
            ValidationError,
            ImproperlyConfigured,
        ) as exception:
            error = str(exception)
        except KeyError:
            logger.exception("Firebase registration response did not contain an ID token.")
            error = "O Firebase retornou uma resposta de cadastro inválida."

    return render(
        request,
        "web/register.html",
        {"form": form, "error": error},
    )


@require_POST
def firebase_logout(request):
    response = redirect("login")
    response.set_cookie(
        SESSION_COOKIE_NAME,
        "",
        max_age=0,
        httponly=True,
        secure=request.is_secure() or not settings.DEBUG,
        path="/",
        samesite="Lax",
    )
    return response


@login_required
def dashboard(request):
    return render(request, "web/dashboard.html")


@login_required
def ticket_list(request):
    if request.user.tipo != "ALUNO":
        raise PermissionDenied
    return render(
        request,
        "web/tickets.html",
        {"tickets": list_tickets(request.user)},
    )


@login_required
def ticket_create(request):
    if request.user.tipo != "ALUNO":
        raise PermissionDenied

    courses = list_active_courses_for_students()
    error = None
    if request.method == "POST":
        try:
            create_ticket(
                request.user,
                request.POST.get("course", ""),
                request.POST.get("subject", ""),
                request.POST.get("description", ""),
            )
            return redirect("ticket_list")
        except ValidationError as exception:
            error = "; ".join(exception.messages)

    return render(
        request,
        "web/ticket_form.html",
        {"courses": courses, "error": error},
    )


@login_required
def monitor_tickets(request):
    if request.user.tipo not in {"MONITOR", "PROFESSOR", "COORDENADOR"}:
        raise PermissionDenied
    return render(
        request,
        "web/monitor_tickets.html",
        {"tickets": list_tickets(request.user)},
    )


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_ticket_for_user(ticket_id, request.user)
    if ticket is None:
        from django.http import Http404

        raise Http404("Dúvida não encontrada.")

    error = None
    can_reply = ticket.status not in {"RESOLVED", "CLOSED"}
    if request.method == "POST":
        try:
            add_message(
                request.user,
                ticket.id,
                request.POST.get("message", ""),
            )
            return redirect("ticket_detail", ticket_id=ticket.id)
        except (PermissionDenied, ValidationError) as exception:
            if isinstance(exception, PermissionDenied):
                raise
            error = "; ".join(exception.messages)

    return render(
        request,
        "web/ticket_detail.html",
        {"ticket": ticket, "can_reply": can_reply, "error": error},
    )


@login_required
def professor_courses(request):
    if request.user.tipo != "PROFESSOR":
        raise PermissionDenied
    return render(
        request,
        "web/professor_courses.html",
        {"courses": list_professor_courses(request.user)},
    )


@login_required
def professor_course_create(request):
    if request.user.tipo != "PROFESSOR":
        raise PermissionDenied

    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            course = create_course(
                form.cleaned_data["code"],
                form.cleaned_data["name"],
                form.cleaned_data["description"],
                request.user,
            )
        except ValidationError as exception:
            form.add_error(None, "; ".join(exception.messages))
        else:
            return redirect(
                "professor_course_assignments",
                course_id=course.id,
            )
    return render(request, "web/course_form.html", {"form": form})


@login_required
def professor_course_assignments(request, course_id):
    if request.user.tipo != "PROFESSOR":
        raise PermissionDenied
    course = get_course(course_id)
    if course is None:
        from django.http import Http404

        raise Http404("Disciplina não encontrada.")

    courses = list_professor_courses(request.user)
    managed_course = next(
        (item for item in courses if item.id == course.id),
        None,
    )
    if managed_course is None:
        from django.http import Http404

        raise Http404("Disciplina não encontrada.")
    course = managed_course

    form = MonitoringAssignmentForm(
        request.POST or None,
        monitors=list_monitors(exclude_course_id=course.id),
    )
    if request.method == "POST" and form.is_valid():
        try:
            assign_monitor(
                course,
                form.cleaned_data["monitor"],
                request.user,
            )
        except (PermissionDenied, ValidationError) as exception:
            if isinstance(exception, PermissionDenied):
                raise
            form.add_error(None, "; ".join(exception.messages))
        else:
            return redirect(
                "professor_course_assignments",
                course_id=course.id,
            )

    return render(
        request,
        "web/course_assignments.html",
        {
            "course": course,
            "form": form,
            "assignments": course.monitorings,
        },
    )
