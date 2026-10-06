from datetime import datetime, timezone
import base64
import json
import os
from unittest import TestCase
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate
from tickets.views import TicketViewSet

from firebase_backend.records import FirebaseUser, MessageRecord
from firebase_backend.repository import (
    add_message,
    assign_monitor,
    create_course,
    create_ticket,
    get_ticket_for_user,
    list_active_courses_for_students,
    list_tickets,
)
from firebase_backend.middleware import FirebaseSessionMiddleware
from firebase_backend.client import firebase_app


class FakeSnapshot:
    def __init__(self, document_id, data):
        self.id = document_id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class FakeDocument:
    def __init__(self, collection, document_id):
        self.collection_ref = collection
        self.id = document_id

    @property
    def data(self):
        return self.collection_ref.documents.get(self.id)

    def get(self):
        return FakeSnapshot(self.id, self.data)

    def create(self, data):
        if self.data is not None:
            raise ValueError("Document already exists.")
        self.collection_ref.documents[self.id] = data

    def set(self, data):
        self.collection_ref.documents[self.id] = data

    def update(self, data):
        self.collection_ref.documents[self.id].update(data)

    def collection(self, name):
        key = (self.collection_ref.name, self.id, name)
        return self.collection_ref.database.subcollections.setdefault(
            key,
            FakeCollection(self.collection_ref.database, name),
        )


class FakeCollection:
    def __init__(self, database, name, filters=(), max_results=None, ordering=None):
        self.database = database
        self.name = name
        self.documents = database.collections.setdefault(name, {})
        self.filters = filters
        self.max_results = max_results
        self.ordering = ordering

    def document(self, document_id=None):
        return FakeDocument(self, document_id or "generated-message")

    def where(self, field, operator, value):
        return FakeCollection(
            self.database,
            self.name,
            (*self.filters, (field, operator, value)),
            self.max_results,
            self.ordering,
        )

    def limit(self, max_results):
        return FakeCollection(
            self.database,
            self.name,
            self.filters,
            max_results,
            self.ordering,
        )

    def order_by(self, field):
        return FakeCollection(
            self.database,
            self.name,
            self.filters,
            self.max_results,
            field,
        )

    def stream(self):
        documents = []
        for document_id, data in self.documents.items():
            if all(
                (data.get(field) == value if operator == "==" else False)
                for field, operator, value in self.filters
            ):
                documents.append(FakeSnapshot(document_id, data))
        if self.ordering:
            documents.sort(
                key=lambda snapshot: snapshot.to_dict().get(self.ordering)
            )
        if self.max_results is not None:
            documents = documents[: self.max_results]
        return iter(documents)


class FakeBatch:
    def __init__(self):
        self.operations = []

    def create(self, reference, data):
        self.operations.append(("create", reference, data))

    def update(self, reference, data):
        self.operations.append(("update", reference, data))

    def commit(self):
        for operation, reference, data in self.operations:
            getattr(reference, operation)(data)


class FakeFirestore:
    def __init__(self):
        self.collections = {}
        self.subcollections = {}

    def collection(self, name):
        return FakeCollection(self, name)

    def batch(self):
        return FakeBatch()


def user(uid, role, username=None):
    return FirebaseUser(
        uid=uid,
        username=username or uid,
        email=f"{uid}@example.test",
        first_name=uid,
        last_name="",
        tipo=role,
    )


def seed_user(database, account):
    database.collection("users").document(account.uid).set(
        {
            "username": account.username,
            "email": account.email,
            "first_name": account.first_name,
            "last_name": account.last_name,
            "tipo": account.tipo,
        }
    )


class FirestoreTicketRepositoryTests(TestCase):
    def setUp(self):
        self.database = FakeFirestore()
        self.student = user("student-uid", "ALUNO", "student")
        self.math_monitor = user("math-monitor-uid", "MONITOR", "math-monitor")
        self.physics_monitor = user("physics-monitor-uid", "MONITOR", "physics-monitor")
        self.professor = user("professor-uid", "PROFESSOR", "professor")
        self.course_math = {
            "code": "MAT",
            "name": "Matemática",
            "description": "",
            "active": True,
            "created_by": self.professor.uid,
        }
        self.course_physics = {
            "code": "FIS",
            "name": "Física",
            "description": "",
            "active": True,
            "created_by": self.professor.uid,
        }
        for account in (
            self.student,
            self.math_monitor,
            self.physics_monitor,
            self.professor,
        ):
            seed_user(self.database, account)
        self.database.collection("courses").document("MAT").set(self.course_math)
        self.database.collection("courses").document("FIS").set(self.course_physics)
        self.database.collection("monitorings").document("math-assignment").set(
            {
                "course_id": "MAT",
                "monitor_uid": self.math_monitor.uid,
                "professor_uid": self.professor.uid,
                "status": "ACTIVE",
            }
        )
        self.database.collection("monitorings").document("physics-assignment").set(
            {
                "course_id": "FIS",
                "monitor_uid": self.physics_monitor.uid,
                "professor_uid": self.professor.uid,
                "status": "ACTIVE",
            }
        )
        now = datetime.now(timezone.utc)
        self.database.collection("tickets").document("math-ticket").set(
            {
                "student_uid": self.student.uid,
                "course_id": "MAT",
                "subject": "Frações",
                "description": "Dúvida em matemática.",
                "status": "OPEN",
                "priority": "MEDIUM",
                "created_at": now,
                "updated_at": now,
            }
        )
        self.database.collection("tickets").document("physics-ticket").set(
            {
                "student_uid": self.student.uid,
                "course_id": "FIS",
                "subject": "Forças",
                "description": "Dúvida em física.",
                "status": "OPEN",
                "priority": "MEDIUM",
                "created_at": now,
                "updated_at": now,
            }
        )

    def test_monitor_only_sees_tickets_for_assigned_course(self):
        with patch("firebase_backend.repository._db", return_value=self.database):
            tickets = list_tickets(self.math_monitor)

        self.assertEqual([ticket.id for ticket in tickets], ["math-ticket"])

    def test_api_serializes_shared_ticket_and_conversation(self):
        with patch("firebase_backend.repository._db", return_value=self.database):
            ticket = list_tickets(self.math_monitor)[0]
            ticket.messages = [
                MessageRecord(
                    id="answer-1",
                    ticket_id=ticket.id,
                    author=self.math_monitor,
                    message="Some os numeradores.",
                    created_at=ticket.created_at,
                )
            ]

        request = APIRequestFactory().get("/api/tickets/")
        force_authenticate(request, user=self.math_monitor)
        with patch("tickets.views.list_tickets", return_value=[ticket]):
            response = TicketViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["course"], "MAT")
        self.assertEqual(
            response.data[0]["messages"][0]["author_name"],
            "math-monitor",
        )

    def test_unassigned_monitor_cannot_read_or_reply_to_another_course(self):
        with patch("firebase_backend.repository._db", return_value=self.database):
            self.assertIsNone(
                get_ticket_for_user("physics-ticket", self.math_monitor)
            )
            with self.assertRaises(PermissionDenied):
                add_message(
                    self.math_monitor,
                    "physics-ticket",
                    "Resposta indevida.",
                )

    def test_monitor_reply_is_atomic_and_marks_shared_ticket_answered(self):
        with patch("firebase_backend.repository._db", return_value=self.database):
            add_message(
                self.math_monitor,
                "math-ticket",
                "Some os numeradores.",
            )

        ticket = self.database.collection("tickets").document("math-ticket").get()
        messages = list(
            self.database.collection("tickets")
            .document("math-ticket")
            .collection("messages")
            .stream()
        )
        self.assertEqual(ticket.to_dict()["status"], "ANSWERED")
        self.assertEqual(messages[0].to_dict()["message"], "Some os numeradores.")

    def test_closed_ticket_rejects_reply(self):
        ticket = self.database.collection("tickets").document("math-ticket")
        ticket.update({"status": "CLOSED"})

        with patch("firebase_backend.repository._db", return_value=self.database):
            with self.assertRaises(ValidationError):
                add_message(self.math_monitor, "math-ticket", "Resposta tardia.")

    def test_student_ticket_is_persisted_in_shared_firestore_collection(self):
        with patch("firebase_backend.repository._db", return_value=self.database):
            ticket = create_ticket(
                self.student,
                "MAT",
                "Equações",
                "Como resolver equações do primeiro grau?",
            )

        stored = self.database.collection("tickets").document(ticket.id).get()
        self.assertEqual(stored.to_dict()["student_uid"], self.student.uid)
        self.assertEqual(stored.to_dict()["course_id"], "MAT")
        self.assertEqual(stored.to_dict()["status"], "OPEN")

    def test_professor_assigns_monitor_and_course_becomes_visible_to_students(self):
        with patch("firebase_backend.repository._db", return_value=self.database):
            course = create_course(
                "QUI",
                "Química",
                "Introdução à química.",
                self.professor,
            )
            assign_monitor(course, self.physics_monitor.uid, self.professor)
            active_courses = list_active_courses_for_students()

        self.assertIn("QUI", {course.id for course in active_courses})
        assignment = self.database.collection("monitorings").document(
            f"QUI_{self.physics_monitor.uid}"
        ).get()
        self.assertEqual(assignment.to_dict()["professor_uid"], self.professor.uid)
        self.assertEqual(assignment.to_dict()["status"], "ACTIVE")


class FirebaseAuthenticationTests(SimpleTestCase):
    def setUp(self):
        self.student = user("student-uid", "ALUNO", "student")

    def test_firebase_cookie_resolves_shared_firestore_profile(self):
        request = RequestFactory().get(
            "/",
            HTTP_COOKIE="firebase_session=valid-cookie",
        )
        with (
            patch(
                "firebase_backend.middleware.verify_session_cookie",
                return_value={"uid": self.student.uid},
            ),
            patch(
                "firebase_backend.middleware.get_user",
                return_value=self.student,
            ),
        ):
            response = FirebaseSessionMiddleware(lambda req: req.user)(request)

        self.assertEqual(response, self.student)

    def test_missing_firebase_cookie_cannot_reuse_legacy_django_login(self):
        request = RequestFactory().get("/")
        request.user = self.student

        response = FirebaseSessionMiddleware(lambda req: req.user)(request)

        self.assertIsInstance(response, AnonymousUser)

    def test_login_page_renders_without_connecting_to_firebase(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="email"')

    @patch("web.views.ensure_student_profile")
    @patch("web.views._set_firebase_cookie")
    @patch("web.views.auth.verify_id_token", return_value={"uid": "created-uid"})
    @patch(
        "web.views.create_user",
        return_value={"idToken": "firebase-id-token"},
    )
    def test_public_registration_creates_only_student_profile(
        self,
        _create_user,
        _verify_token,
        set_cookie,
        create_profile,
    ):
        set_cookie.return_value = HttpResponseRedirect("/")
        client = self.client
        result = client.post(
            reverse("register"),
            {
                "first_name": "Novo",
                "last_name": "Aluno",
                "email": "novo@example.test",
                "password": "Valid-Test-Password-238!",
                "password_confirm": "Valid-Test-Password-238!",
                "tipo": "PROFESSOR",
            },
        )

        self.assertEqual(result.status_code, 302)
        self.assertTrue(_create_user.called)
        self.assertTrue(_verify_token.called)
        create_profile.assert_called_once_with(
            "created-uid",
            "novo@example.test",
            "Novo",
            "Aluno",
        )


class FirebaseCredentialsTests(SimpleTestCase):
    def test_base64_service_account_is_loaded_without_logging_credentials(self):
        service_account_info = {
            "project_id": "monitoria-test",
            "private_key": "test-private-key",
        }
        encoded = base64.b64encode(
            json.dumps(service_account_info).encode("utf-8")
        ).decode("ascii")
        credential = object()
        app = object()

        with (
            patch.dict(
                os.environ,
                {
                    "FIREBASE_PROJECT_ID": "monitoria-test",
                    "FIREBASE_SERVICE_ACCOUNT_BASE64": encoded,
                },
                clear=False,
            ),
            patch(
                "firebase_backend.client.firebase_admin.get_app",
                side_effect=ValueError,
            ),
            patch(
                "firebase_backend.client.credentials.Certificate",
                return_value=credential,
            ) as certificate,
            patch(
                "firebase_backend.client.firebase_admin.initialize_app",
                return_value=app,
            ) as initialize,
        ):
            result = firebase_app()

        self.assertIs(result, app)
        certificate.assert_called_once_with(service_account_info)
        initialize.assert_called_once_with(
            credential=credential,
            options={"projectId": "monitoria-test"},
        )

    def test_malformed_service_account_fails_without_echoing_its_value(self):
        invalid_value = "not-a-valid-private-credential"
        with (
            patch.dict(
                os.environ,
                {
                    "FIREBASE_PROJECT_ID": "monitoria-test",
                    "FIREBASE_SERVICE_ACCOUNT_BASE64": invalid_value,
                },
                clear=False,
            ),
            patch(
                "firebase_backend.client.firebase_admin.get_app",
                side_effect=ValueError,
            ),
        ):
            with self.assertRaises(ImproperlyConfigured) as caught:
                firebase_app()

        self.assertNotIn(invalid_value, str(caught.exception))

    def test_service_account_must_match_configured_firebase_project(self):
        encoded = base64.b64encode(
            json.dumps({"project_id": "another-project"}).encode("utf-8")
        ).decode("ascii")
        with (
            patch.dict(
                os.environ,
                {
                    "FIREBASE_PROJECT_ID": "monitoria-test",
                    "FIREBASE_SERVICE_ACCOUNT_BASE64": encoded,
                },
                clear=False,
            ),
            patch(
                "firebase_backend.client.firebase_admin.get_app",
                side_effect=ValueError,
            ),
            patch(
                "firebase_backend.client.credentials.Certificate"
            ) as certificate,
        ):
            with self.assertRaises(ImproperlyConfigured):
                firebase_app()

        certificate.assert_not_called()

    def test_production_requires_service_account_credentials(self):
        with (
            patch("firebase_backend.client.settings.DEBUG", False),
            patch.dict(
                os.environ,
                {"FIREBASE_PROJECT_ID": "monitoria-test"},
                clear=False,
            ),
            patch.dict(
                os.environ,
                {"FIREBASE_SERVICE_ACCOUNT_BASE64": ""},
                clear=False,
            ),
            patch(
                "firebase_backend.client.firebase_admin.get_app",
                side_effect=ValueError,
            ),
        ):
            with self.assertRaises(ImproperlyConfigured) as caught:
                firebase_app()

        self.assertIn(
            "FIREBASE_SERVICE_ACCOUNT_BASE64",
            str(caught.exception),
        )
