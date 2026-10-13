from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.models import Course
from monitoring.models import Monitoring
from users.models import User

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
