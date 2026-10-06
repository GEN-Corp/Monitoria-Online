from getpass import getpass

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from firebase_admin import auth

from firebase_backend.repository import (
    assign_monitor,
    create_course,
    create_user_profile,
    get_course_by_code,
    get_user,
)


DEMO_USERS = (
    ("demo_professor", "demo_professor@example.com", "Professor", "PROFESSOR"),
    ("demo_student", "demo_student@example.com", "Aluno", "ALUNO"),
    (
        "demo_monitor_informatica",
        "demo_monitor_informatica@example.com",
        "Monitor de Informática",
        "MONITOR",
    ),
    (
        "demo_monitor_fisica",
        "demo_monitor_fisica@example.com",
        "Monitor de Física",
        "MONITOR",
    ),
    (
        "demo_monitor_quimica",
        "demo_monitor_quimica@example.com",
        "Monitor de Química",
        "MONITOR",
    ),
    (
        "demo_monitor_matematica",
        "demo_monitor_matematica@example.com",
        "Monitor de Matemática",
        "MONITOR",
    ),
    (
        "demo_monitor_biologia",
        "demo_monitor_biologia@example.com",
        "Monitor de Biologia",
        "MONITOR",
    ),
)

DEMO_COURSES = (
    ("DEMO-INF", "Informática", "Fundamentos de informática.", "demo_monitor_informatica"),
    ("DEMO-FIS", "Física", "Conteúdos introdutórios de física.", "demo_monitor_fisica"),
    ("DEMO-QUI", "Química", "Conteúdos introdutórios de química.", "demo_monitor_quimica"),
    ("DEMO-MAT", "Matemática", "Conteúdos introdutórios de matemática.", "demo_monitor_matematica"),
    ("DEMO-BIO", "Biologia", "Conteúdos introdutórios de biologia.", "demo_monitor_biologia"),
)


class Command(BaseCommand):
    help = "Cria contas Firebase e disciplinas de demonstração no Firestore."

    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            required=True,
            help="ID exato do projeto Firebase que receberá os dados de teste.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Dados de demonstração só podem ser criados em ambiente local."
            )
        if options["project_id"] != settings.FIREBASE_PROJECT_ID:
            raise CommandError(
                "O ID informado precisa corresponder a FIREBASE_PROJECT_ID no .env."
            )
        _ = args
        password = getpass("Defina a senha local para as contas de demonstração: ")
        confirmation = getpass("Confirme a senha: ")
        if len(password) < 8:
            raise CommandError("A senha precisa ter pelo menos 8 caracteres.")
        if password != confirmation:
            raise CommandError("As senhas digitadas não coincidem.")

        users = {}
        for username, email, first_name, role in DEMO_USERS:
            try:
                firebase_user = auth.get_user_by_email(email)
                auth.update_user(
                    firebase_user.uid,
                    password=password,
                    display_name=first_name,
                    disabled=False,
                )
            except auth.UserNotFoundError:
                firebase_user = auth.create_user(
                    email=email,
                    password=password,
                    display_name=first_name,
                )
            create_user_profile(
                firebase_user.uid,
                username,
                email,
                first_name,
                role,
            )
            users[username] = get_user(firebase_user.uid)

        professor = users["demo_professor"]
        for code, name, description, monitor_username in DEMO_COURSES:
            course = get_course_by_code(code)
            if course is None:
                course = create_course(code, name, description, professor)
            monitor = users[monitor_username]
            assign_monitor(course, monitor.uid, professor)

        self.stdout.write(
            self.style.SUCCESS(
                "Contas Firebase e dados de demonstração preparados."
            )
        )
        self.stdout.write("Usuários disponíveis:")
        for username, email, _, _ in DEMO_USERS:
            self.stdout.write(f"  {username} ({email})")
        self.stdout.write(
            "As senhas foram definidas localmente e não foram exibidas."
        )
