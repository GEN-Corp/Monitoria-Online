import os

import firebase_admin
from django.core.exceptions import ImproperlyConfigured
from firebase_admin import firestore


def firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        if not project_id:
            raise ImproperlyConfigured(
                "FIREBASE_PROJECT_ID precisa ser configurado para usar o Firebase."
            )
        return firebase_admin.initialize_app(options={"projectId": project_id})


def firestore_client():
    return firestore.client(firebase_app())
