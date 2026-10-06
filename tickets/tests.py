from datetime import date
from io import StringIO
from secrets import token_urlsafe
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from courses.models import Course
from monitoring.models import Monitoring
from users.models import User
from tickets.querysets import tickets_for_user

from .models import Ticket, TicketMessage


class TicketConversationTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="aluno",
            password="password",
            tipo=User.TipoUsuario.ALUNO,
        )
        self.monitor = User.objects.create_user(
            username="monitor",
            password="password",
            tipo=User.TipoUsuario.MONITOR,
        )
        self.professor = User.objects.create_user(
            username="professor",
            password="password",
            tipo=User.TipoUsuario.PROFESSOR,
        )
        self.other_monitor = User.objects.create_user(
            username="outro-monitor",
            password="password",
            tipo=User.TipoUsuario.MONITOR,
        )
        self.course = Course.objects.create(
            name="Matemática",
            code="MAT101",
        )
        Monitoring.objects.create(
            course=self.course,
            monitor=self.monitor,
            professor=self.professor,
            status=Monitoring.Status.ACTIVE,
            start_date=date.today(),
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            course=self.course,
            subject="Frações",
            description="Como somo frações?",
        )

    def test_assigned_staff_sees_course_ticket_without_monitoring_fk(self):
        self.client.force_login(self.monitor)

        response = self.client.get(reverse("monitor_tickets"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frações")

    def test_staff_answer_is_shown_to_student_as_answered(self):
        self.client.force_login(self.monitor)
        response = self.client.post(
            reverse("ticket_detail", args=[self.ticket.pk]),
            {"message": "Some os numeradores após igualar os denominadores."},
        )

        self.assertRedirects(
            response,
            reverse("ticket_detail", args=[self.ticket.pk]),
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.ANSWERED)
        self.assertTrue(
            TicketMessage.objects.filter(
                ticket=self.ticket,
                author=self.monitor,
            ).exists()
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("ticket_list"))
        self.assertContains(response, "Respondido")
        self.assertContains(response, "Ver conversa")

        response = self.client.get(
            reverse("ticket_detail", args=[self.ticket.pk])
        )
        self.assertContains(
            response,
            "Some os numeradores após igualar os denominadores.",
        )

    def test_unassigned_monitor_cannot_view_course_ticket(self):
        self.client.force_login(self.other_monitor)

        response = self.client.get(
            reverse("ticket_detail", args=[self.ticket.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_open_ticket_for_course_without_active_monitoring(self):
        unstaffed_course = Course.objects.create(
            name="Física",
            code="FIS101",
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("ticket_create"),
            {
                "course": unstaffed_course.pk,
                "subject": "Dúvida sem destinatário",
                "description": "Esta dúvida não deve ser criada.",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Ticket.objects.filter(
                subject="Dúvida sem destinatário"
            ).exists()
        )

    def test_api_staff_reply_updates_ticket_status(self):
        client = APIClient()
        client.force_authenticate(user=self.professor)

        response = client.post(
            reverse("message-list"),
            {
                "ticket": self.ticket.pk,
                "message": "Vamos revisar esse conteúdo na monitoria.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.ANSWERED)

    def test_api_student_cannot_open_ticket_without_active_monitoring(self):
        course_without_monitor = Course.objects.create(
            name="Astronomia",
            code="AST101",
        )
        client = APIClient()
        client.force_authenticate(user=self.student)

        response = client.post(
            reverse("ticket-list"),
            {
                "course": course_without_monitor.pk,
                "subject": "Planetas",
                "description": "Dúvida sem monitoria.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            Ticket.objects.filter(course=course_without_monitor).exists()
        )

    def test_monitor_cannot_view_ticket_from_another_discipline(self):
        another_course = Course.objects.create(
            name="Química",
            code="QUI101",
        )
        Monitoring.objects.create(
            course=another_course,
            monitor=self.other_monitor,
            professor=self.professor,
            status=Monitoring.Status.ACTIVE,
            start_date=date.today(),
        )
        another_ticket = Ticket.objects.create(
            student=self.student,
            course=another_course,
            subject="Ligações químicas",
            description="Dúvida da outra disciplina.",
        )
        self.client.force_login(self.monitor)

        response = self.client.get(
            reverse("ticket_detail", args=[another_ticket.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Ticket.objects.filter(
                pk__in=tickets_for_user(self.monitor).values("pk")
            ).filter(pk=another_ticket.pk).exists()
        )

    def test_monitor_cannot_reply_to_ticket_from_another_discipline_via_api(self):
        another_course = Course.objects.create(
            name="Química",
            code="QUI102",
        )
        Monitoring.objects.create(
            course=another_course,
            monitor=self.other_monitor,
            professor=self.professor,
            status=Monitoring.Status.ACTIVE,
            start_date=date.today(),
        )
        another_ticket = Ticket.objects.create(
            student=self.student,
            course=another_course,
            subject="Reações",
            description="Dúvida de química.",
        )
        client = APIClient()
        client.force_authenticate(user=self.monitor)

        response = client.post(
            reverse("message-list"),
            {
                "ticket": another_ticket.pk,
                "message": "Esta resposta não deve ser aceita.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            TicketMessage.objects.filter(ticket=another_ticket).exists()
        )

    def test_ticket_api_does_not_allow_editing_after_creation(self):
        client = APIClient()
        client.force_authenticate(user=self.monitor)

        response = client.patch(
            reverse("ticket-detail", args=[self.ticket.pk]),
            {"subject": "Assunto alterado"},
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def test_professor_can_create_course_and_assign_monitor(self):
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse("professor_course_create"),
            {
                "code": "INF201",
                "name": "Informática Aplicada",
                "description": "Conteúdo de informática.",
            },
        )
        course = Course.objects.get(code="INF201")
        self.assertEqual(course.created_by, self.professor)
        self.assertRedirects(
            response,
            reverse(
                "professor_course_assignments",
                args=[course.pk],
            ),
        )

        response = self.client.post(
            reverse("professor_course_assignments", args=[course.pk]),
            {"monitor": self.monitor.pk},
        )

        self.assertRedirects(
            response,
            reverse(
                "professor_course_assignments",
                args=[course.pk],
            ),
        )
        self.assertTrue(
            Monitoring.objects.filter(
                course=course,
                professor=self.professor,
                monitor=self.monitor,
                status=Monitoring.Status.ACTIVE,
            ).exists()
        )

    def test_professor_cannot_manage_another_professors_course(self):
        course = Course.objects.create(
            name="Física avançada",
            code="FIS201",
            created_by=self.professor,
        )
        another_professor = User.objects.create_user(
            username="outro-professor",
            password="valid-test-password",
            tipo=User.TipoUsuario.PROFESSOR,
        )
        course.created_by = another_professor
        course.save(update_fields=["created_by"])
        self.client.force_login(self.professor)

        response = self.client.get(
            reverse("professor_course_assignments", args=[course.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_public_registration_always_creates_student(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "publico",
                "first_name": "Usuário",
                "last_name": "Teste",
                "email": "publico@example.invalid",
                "password": "Public-test-password-823!",
                "password_confirm": "Public-test-password-823!",
                "tipo": User.TipoUsuario.PROFESSOR,
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="publico")
        self.assertEqual(user.tipo, User.TipoUsuario.ALUNO)

    @override_settings(DEBUG=True)
    def test_seed_demo_creates_disciplines_and_role_accounts(self):
        password = f"Demo-Only-{token_urlsafe(16)}!"
        with patch(
            "courses.management.commands.seed_demo.getpass",
            side_effect=[password, password],
        ) as getpass_mock:
            output = StringIO()
            call_command("seed_demo", stdout=output)

        self.assertEqual(Course.objects.filter(code__startswith="DEMO-").count(), 5)
        self.assertEqual(
            Monitoring.objects.filter(
                course__code__startswith="DEMO-",
                status=Monitoring.Status.ACTIVE,
            ).count(),
            5,
        )
        for code, username in (
            ("DEMO-INF", "demo_monitor_informatica"),
            ("DEMO-FIS", "demo_monitor_fisica"),
            ("DEMO-QUI", "demo_monitor_quimica"),
            ("DEMO-MAT", "demo_monitor_matematica"),
            ("DEMO-BIO", "demo_monitor_biologia"),
        ):
            self.assertTrue(
                Monitoring.objects.filter(
                    course__code=code,
                    monitor__username=username,
                    status=Monitoring.Status.ACTIVE,
                ).exists()
            )
        self.assertEqual(
            User.objects.get(username="demo_professor").tipo,
            User.TipoUsuario.PROFESSOR,
        )
        self.assertEqual(
            User.objects.get(username="demo_monitor_informatica").tipo,
            User.TipoUsuario.MONITOR,
        )
        self.assertEqual(getpass_mock.call_count, 2)
        self.assertNotIn(password, output.getvalue())
