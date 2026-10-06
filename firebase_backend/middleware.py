import logging

from django.contrib.auth.models import AnonymousUser
from firebase_admin import auth

from .identity import SESSION_COOKIE_NAME, verify_session_cookie
from .repository import get_user


logger = logging.getLogger(__name__)


class FirebaseSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = AnonymousUser()
        session_cookie = request.COOKIES.get(SESSION_COOKIE_NAME)
        if session_cookie:
            try:
                claims = verify_session_cookie(session_cookie)
            except (
                auth.InvalidSessionCookieError,
                auth.RevokedSessionCookieError,
                auth.ExpiredSessionCookieError,
            ):
                logger.info("Rejected an invalid Firebase session cookie.")
                request.user = AnonymousUser()
            else:
                user = get_user(claims["uid"])
                if user is None:
                    logger.warning(
                        "Firebase identity has no matching Firestore user profile."
                    )
                    request.user = AnonymousUser()
                else:
                    request.user = user

        return self.get_response(request)
