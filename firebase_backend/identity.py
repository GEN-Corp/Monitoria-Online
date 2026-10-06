import json
import logging
import os
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from firebase_admin import auth


logger = logging.getLogger(__name__)
SESSION_COOKIE_NAME = "firebase_session"
SESSION_DURATION = timedelta(days=5)


class FirebaseIdentityError(Exception):
    pass


def _identity_request(method, payload):
    api_key = getattr(settings, "FIREBASE_API_KEY", "")
    if not api_key:
        raise ImproperlyConfigured(
            "FIREBASE_API_KEY precisa ser configurado para login e cadastro."
        )

    emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
    base_url = (
        f"http://{emulator_host}/identitytoolkit.googleapis.com"
        if emulator_host
        else "https://identitytoolkit.googleapis.com"
    )
    request = Request(
        f"{base_url}/v1/accounts:{method}?{urlencode({'key': api_key})}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            detail = json.loads(error.read().decode("utf-8"))
            firebase_error = detail.get("error", {}).get("message", "UNKNOWN")
        except (json.JSONDecodeError, UnicodeDecodeError):
            firebase_error = "UNKNOWN"
        logger.info("Firebase Identity Toolkit rejected %s (%s)", method, firebase_error)
        raise FirebaseIdentityError(
            "E-mail ou senha inválidos, ou não foi possível concluir a operação."
        ) from error
    except (TimeoutError, URLError) as error:
        logger.exception("Firebase Identity Toolkit request failed")
        raise FirebaseIdentityError(
            "Não foi possível conectar ao Firebase. Tente novamente."
        ) from error


def create_user(email, password):
    return _identity_request(
        "signUp",
        {"email": email, "password": password, "returnSecureToken": True},
    )


def sign_in(email, password):
    return _identity_request(
        "signInWithPassword",
        {"email": email, "password": password, "returnSecureToken": True},
    )


def create_session_cookie(id_token):
    return auth.create_session_cookie(
        id_token,
        expires_in=SESSION_DURATION,
    )


def verify_session_cookie(cookie):
    return auth.verify_session_cookie(cookie, check_revoked=True)
