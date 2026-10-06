from datetime import date
from getpass import getpass

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.models import Course
from monitoring.models import Monitoring
from users.models import User


DEMO_USERS = {
    "demo_professor": ("Professor", User.TipoUsuario.PROFESSOR),
    "demo_student": ("Aluno", User.TipoUsuario.ALUNO),
    "demo_monitor_informatica": ("Monitor de Informática", User.TipoUsuario.MONITOR),
    "demo_monitor_fisica": ("Monitor de Física", User.TipoUsuario.MONITOR),
    "demo_monitor_quimica": ("Monitor de Química", User.TipoUsuario.MONITOR),
    "demo_monitor_matematica": ("Monitor de Matemática", User.TipoUsuario.MONITOR),
    "demo_monitor_biologia": ("Monitor de Biologia", User.TipoUsuario.MONITOR),
}

DEMO_COURSES = (
    ("DEMO-INF", "Informática", "Fundamentos de informática.", "demo_monitor_informatica"),
    ("DEMO-FIS", "Física", "Conteúdos introdutórios de física.", "demo_monitor_fisica"),
    ("DEMO-QUI", "Química", "Conteúdos introdutórios de química.", "demo_monitor_quimica"),
    ("DEMO-MAT", "Matemática", "Conteúdos introdutórios de matemática.", "demo_monitor_matematica"),
    ("DEMO-BIO", "Biologia", "Conteúdos introdutórios de biologia.", "demo_monitor_biologia"),
)


class Command(BaseCommand):
    help = "Cria contas, disciplinas e monitorias de demonstração."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Dados de demonstração só podem ser criados em ambiente local."
            )
        _ = args, options
        password = getpass("Defina a senha local para as contas de demonstração: ")
        confirmation = getpass("Confirme a senha: ")
        if not password:
            raise CommandError("A senha não pode ficar vazia.")
        if password != confirmation:
            raise CommandError("As senhas digitadas não coincidem.")
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        with transaction.atomic():
            users = {}
            for username, (first_name, role) in DEMO_USERS.items():
                email = f"{username}@example.invalid"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "first_name": first_name,
                        "last_name": "Demonstração",
                        "email": email,
                        "tipo": role,
                    },
                )
                if not created and (
                    user.email != email
                    or user.is_staff
                    or user.is_superuser
                ):
                    raise CommandError(
                        f"O usuário reservado {username} já pertence a outra conta."
                    )
                user.first_name = first_name
                user.last_name = "Demonstração"
                user.email = email
                user.tipo = role
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user.set_password(password)
                user.save()
                users[username] = user

            professor = users["demo_professor"]
            for code, name, description, monitor_username in DEMO_COURSES:
                course, _ = Course.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "description": description,
                        "active": True,
                        "created_by": professor,
                    },
                )
                monitor = users[monitor_username]
                Monitoring.objects.update_or_create(
                    course=course,
                    monitor=monitor,
                    professor=professor,
                    defaults={
                        "status": Monitoring.Status.ACTIVE,
                        "start_date": date.today(),
                        "end_date": None,
                        "description": "Monitoria de demonstração.",
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Dados de demonstração criados. A senha foi definida localmente "
                "e não foi exibida."
            )
        )
        self.stdout.write("Usuários disponíveis:")
        for username in DEMO_USERS:
            self.stdout.write(f"  {username}")
