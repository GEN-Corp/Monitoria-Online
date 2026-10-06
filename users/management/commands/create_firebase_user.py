from getpass import getpass

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from firebase_admin import auth

from firebase_backend.repository import (
    create_user_profile,
    get_user,
    username_exists,
)


USER_ROLES = ("ALUNO", "MONITOR", "PROFESSOR", "COORDENADOR")


class Command(BaseCommand):
    help = "Cria uma conta Firebase e seu perfil de usuário no Firestore."

    def add_arguments(self, parser):
        parser.add_argument("--project-id", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--username", required=True)
        parser.add_argument("--first-name", required=True)
        parser.add_argument("--role", choices=USER_ROLES, required=True)

    def handle(self, *args, **options):
        _ = args
        if options["project_id"] != settings.FIREBASE_PROJECT_ID:
            raise CommandError(
                "O ID informado precisa corresponder a FIREBASE_PROJECT_ID."
            )
        if username_exists(options["username"]):
            raise CommandError("Já existe um perfil com esse nome de usuário.")

        password = getpass("Defina uma senha para a conta: ")
        confirmation = getpass("Confirme a senha: ")
        if len(password) < 8:
            raise CommandError("A senha precisa ter pelo menos 8 caracteres.")
        if password != confirmation:
            raise CommandError("As senhas digitadas não coincidem.")

        try:
            auth.get_user_by_email(options["email"])
        except auth.UserNotFoundError:
            pass
        else:
            raise CommandError(
                "Já existe uma conta Firebase com esse e-mail; nenhuma senha foi alterada."
            )

        firebase_user = auth.create_user(
            email=options["email"],
            password=password,
            display_name=options["first_name"],
        )
        if get_user(firebase_user.uid) is not None:
            auth.delete_user(firebase_user.uid)
            raise CommandError(
                "Já existe um perfil Firestore para essa nova conta; a conta Auth foi removida."
            )
        create_user_profile(
            firebase_user.uid,
            options["username"],
            options["email"],
            options["first_name"],
            options["role"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Conta {options['username']} criada no projeto Firebase."
            )
        )
