import base64
import binascii
import json
import os

import firebase_admin
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from firebase_admin import credentials
from firebase_admin import firestore


def _firebase_credentials():
    encoded_credentials = os.environ.get("FIREBASE_SERVICE_ACCOUNT_BASE64")
    if not encoded_credentials:
        return None

    try:
        decoded_credentials = base64.b64decode(
            encoded_credentials,
            validate=True,
        )
        service_account_info = json.loads(decoded_credentials)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ImproperlyConfigured(
            "FIREBASE_SERVICE_ACCOUNT_BASE64 precisa conter uma chave de "
            "conta de serviço Firebase em Base64 válida."
        ) from error

    if not isinstance(service_account_info, dict):
        raise ImproperlyConfigured(
            "A credencial Firebase precisa ser um objeto JSON."
        )
    if service_account_info.get("project_id") != os.environ.get(
        "FIREBASE_PROJECT_ID"
    ):
        raise ImproperlyConfigured(
            "A conta de serviço e FIREBASE_PROJECT_ID precisam ser do mesmo projeto."
        )
    try:
        return credentials.Certificate(service_account_info)
    except (KeyError, ValueError) as error:
        raise ImproperlyConfigured(
            "FIREBASE_SERVICE_ACCOUNT_BASE64 não contém uma credencial Firebase válida."
        ) from error


def firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        if not project_id:
            raise ImproperlyConfigured(
                "FIREBASE_PROJECT_ID precisa ser configurado para usar o Firebase."
            )
        if not settings.DEBUG and not os.environ.get(
            "FIREBASE_SERVICE_ACCOUNT_BASE64"
        ):
            raise ImproperlyConfigured(
                "Configure FIREBASE_SERVICE_ACCOUNT_BASE64 nas variáveis protegidas "
                "da hospedagem."
            )
        return firebase_admin.initialize_app(
            credential=_firebase_credentials(),
            options={"projectId": project_id},
        )


def firestore_client():
    return firestore.client(firebase_app())
