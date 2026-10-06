import re
from datetime import datetime, time, timezone
from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from google.api_core.exceptions import AlreadyExists

from .client import firestore_client
from .records import (
    CourseRecord,
    FirebaseUser,
    MessageRecord,
    MonitoringRecord,
    TicketRecord,
)


USER_ROLES = {"ALUNO", "MONITOR", "PROFESSOR", "COORDENADOR"}
TICKET_STATUSES = {"OPEN", "IN_PROGRESS", "ANSWERED", "RESOLVED", "CLOSED"}
PRIORITIES = {"LOW", "MEDIUM", "HIGH"}


def _db():
    return firestore_client()


def _record_user(uid, data):
    return FirebaseUser(
        uid=uid,
        username=data.get("username") or data.get("email", uid),
        email=data.get("email", ""),
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        tipo=data.get("tipo", ""),
    )


def get_user(uid):
    snapshot = _db().collection("users").document(uid).get()
    if not snapshot.exists:
        return None
    return _record_user(snapshot.id, snapshot.to_dict())


def create_student_profile(uid, email, first_name, last_name):
    user_ref = _db().collection("users").document(uid)
    user_ref.create(
        {
            "uid": uid,
            "username": email.split("@", maxsplit=1)[0],
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tipo": "ALUNO",
            "created_at": datetime.now(timezone.utc),
        }
    )
    return get_user(uid)


def ensure_student_profile(uid, email, first_name="", last_name=""):
    user = get_user(uid)
    if user is not None:
        return user
    try:
        return create_student_profile(uid, email, first_name, last_name)
    except AlreadyExists:
        user = get_user(uid)
        if user is None:
            raise
        return user


def create_user_profile(uid, username, email, first_name, tipo):
    if tipo not in USER_ROLES:
        raise ValidationError("Perfil de usuário inválido.")
    _db().collection("users").document(uid).set(
        {
            "uid": uid,
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": "",
            "tipo": tipo,
            "created_at": datetime.now(timezone.utc),
        }
    )


def username_exists(username):
    return bool(
        list(
            _db()
            .collection("users")
            .where("username", "==", username)
            .limit(1)
            .stream()
        )
    )


def _course_record(snapshot):
    data = snapshot.to_dict()
    return CourseRecord(
        id=snapshot.id,
        name=data["name"],
        code=data["code"],
        description=data.get("description", ""),
        active=data.get("active", True),
        created_by=data.get("created_by", ""),
    )


def list_courses(active_only=False):
    query = _db().collection("courses")
    if active_only:
        query = query.where("active", "==", True)
    records = [_course_record(doc) for doc in query.stream()]
    records.sort(key=lambda course: (course.code, course.name))
    return records


def get_course(course_id):
    snapshot = _db().collection("courses").document(str(course_id)).get()
    if not snapshot.exists:
        return None
    return _course_record(snapshot)


def get_course_by_code(code):
    docs = list(
        _db()
        .collection("courses")
        .where("code", "==", code)
        .limit(1)
        .stream()
    )
    return _course_record(docs[0]) if docs else None


def _user_or_missing(uid):
    user = get_user(uid)
    if user is None:
        raise ValidationError("A conta associada à monitoria não existe.")
    return user


def _monitoring_record(snapshot):
    data = snapshot.to_dict()
    return MonitoringRecord(
        id=snapshot.id,
        course_id=data["course_id"],
        monitor_id=data["monitor_uid"],
        professor_id=data["professor_uid"],
        monitor=_user_or_missing(data["monitor_uid"]),
        professor=_user_or_missing(data["professor_uid"]),
        status=data.get("status", "ACTIVE"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        description=data.get("description", ""),
    )


def list_monitorings(
    course_id=None,
    professor_uid=None,
    monitor_uid=None,
    active_only=False,
):
    query = _db().collection("monitorings")
    if course_id is not None:
        query = query.where("course_id", "==", str(course_id))
    if professor_uid is not None:
        query = query.where("professor_uid", "==", professor_uid)
    if monitor_uid is not None:
        query = query.where("monitor_uid", "==", monitor_uid)
    if active_only:
        query = query.where("status", "==", "ACTIVE")
    records = [_monitoring_record(doc) for doc in query.stream()]
    records.sort(key=lambda item: (str(item.start_date), item.monitor.username))
    return records


def list_active_courses_for_students():
    ids = {
        doc.to_dict()["course_id"]
        for doc in _db()
        .collection("monitorings")
        .where("status", "==", "ACTIVE")
        .stream()
    }
    return [course for course in list_courses(active_only=True) if course.id in ids]


def create_course(code, name, description, professor):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", code):
        raise ValidationError("O código deve conter até 20 letras, números, _ ou -.")
    if get_course_by_code(code):
        raise ValidationError("Já existe uma disciplina com esse código.")

    document_id = code.upper()
    try:
        _db().collection("courses").document(document_id).create(
            {
                "code": code.upper(),
                "name": name.strip(),
                "description": description.strip(),
                "active": True,
                "created_by": professor.uid,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except AlreadyExists as error:
        raise ValidationError(
            "Já existe uma disciplina com esse código."
        ) from error
    return get_course(document_id)


def list_professor_courses(professor):
    all_courses = list_courses()
    courses = [course for course in all_courses if course.created_by == professor.uid]
    monitorings = list_monitorings(professor_uid=professor.uid)
    course_ids = {item.course_id for item in monitorings}
    known = {course.id for course in courses}
    courses.extend(
        course for course in all_courses if course.id in course_ids - known
    )
    for course in courses:
        course.monitorings = [
            item for item in monitorings if item.course_id == course.id
        ]
    return courses


def assign_monitor(course, monitor_uid, professor):
    if course.created_by != professor.uid and not any(
        item.professor_id == professor.uid
        for item in list_monitorings(course_id=course.id)
    ):
        raise PermissionDenied("Você não pode gerenciar esta disciplina.")
    monitor = _user_or_missing(monitor_uid)
    if monitor.tipo != "MONITOR":
        raise ValidationError("A conta selecionada não é de um monitor.")

    document_id = f"{course.id}_{monitor.uid}"
    _db().collection("monitorings").document(document_id).set(
        {
            "course_id": course.id,
            "monitor_uid": monitor.uid,
            "professor_uid": professor.uid,
            "status": "ACTIVE",
            "start_date": datetime.combine(
                datetime.now(timezone.utc).date(),
                time.min,
                tzinfo=timezone.utc,
            ),
            "end_date": None,
            "description": "Monitoria cadastrada pelo professor.",
        }
    )


def list_monitors(exclude_course_id=None):
    assigned = set()
    if exclude_course_id is not None:
        assigned = {
            item.monitor_id
            for item in list_monitorings(
                course_id=exclude_course_id,
                active_only=True,
            )
        }
    users = []
    for snapshot in _db().collection("users").where("tipo", "==", "MONITOR").stream():
        user = _record_user(snapshot.id, snapshot.to_dict())
        if user.uid not in assigned:
            users.append(user)
    users.sort(key=lambda user: user.username)
    return users


def _ticket_record(snapshot, include_messages=False):
    data = snapshot.to_dict()
    student = _user_or_missing(data["student_uid"])
    course = get_course(data["course_id"])
    if course is None:
        raise ValidationError("A disciplina da dúvida não existe.")
    messages = list_messages(snapshot.id) if include_messages else []
    return TicketRecord(
        id=snapshot.id,
        student=student,
        course=course,
        subject=data["subject"],
        description=data["description"],
        status=data.get("status", "OPEN"),
        priority=data.get("priority", "MEDIUM"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        messages=messages,
    )


def ticket_is_visible(user, ticket_data):
    if user.tipo == "ALUNO":
        return ticket_data.get("student_uid") == user.uid
    if user.tipo in {"COORDENADOR"} or user.is_superuser:
        return True
    if user.tipo not in {"MONITOR", "PROFESSOR"}:
        return False

    assignments = list_monitorings(
        course_id=ticket_data["course_id"],
        active_only=True,
        monitor_uid=user.uid if user.tipo == "MONITOR" else None,
        professor_uid=user.uid if user.tipo == "PROFESSOR" else None,
    )
    return bool(assignments)


def list_tickets(user, include_messages=False):
    if user.tipo == "ALUNO":
        snapshots = _db().collection("tickets").where(
            "student_uid", "==", user.uid
        ).stream()
    elif user.tipo in {"MONITOR", "PROFESSOR"}:
        assignments = list_monitorings(
            monitor_uid=user.uid if user.tipo == "MONITOR" else None,
            professor_uid=user.uid if user.tipo == "PROFESSOR" else None,
            active_only=True,
        )
        course_ids = {assignment.course_id for assignment in assignments}
        snapshots = [
            snapshot
            for course_id in course_ids
            for snapshot in _db()
            .collection("tickets")
            .where("course_id", "==", course_id)
            .stream()
        ]
    elif user.tipo == "COORDENADOR" or user.is_superuser:
        snapshots = _db().collection("tickets").stream()
    else:
        return []
    records = [
        _ticket_record(doc, include_messages=include_messages)
        for doc in snapshots
    ]
    records.sort(
        key=lambda ticket: ticket.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return records


def get_ticket_for_user(ticket_id, user, include_messages=True):
    snapshot = _db().collection("tickets").document(str(ticket_id)).get()
    if not snapshot.exists:
        return None
    data = snapshot.to_dict()
    if not ticket_is_visible(user, data):
        return None
    return _ticket_record(snapshot, include_messages=include_messages)


def create_ticket(student, course_id, subject, description):
    course = get_course(course_id)
    if course is None or not course.active:
        raise ValidationError("Selecione uma disciplina ativa.")
    if not list_monitorings(course_id=course.id, active_only=True):
        raise ValidationError("A disciplina não possui monitoria ativa.")
    subject = subject.strip()
    description = description.strip()
    if not subject or len(subject) > 200 or not description:
        raise ValidationError("Informe um assunto e descreva sua dúvida.")

    now = datetime.now(timezone.utc)
    document_id = str(uuid4())
    _db().collection("tickets").document(document_id).create(
        {
            "student_uid": student.uid,
            "course_id": course.id,
            "subject": subject,
            "description": description,
            "status": "OPEN",
            "priority": "MEDIUM",
            "created_at": now,
            "updated_at": now,
        }
    )
    return get_ticket_for_user(document_id, student)


def list_messages(ticket_id):
    snapshots = (
        _db()
        .collection("tickets")
        .document(str(ticket_id))
        .collection("messages")
        .order_by("created_at")
        .stream()
    )
    messages = []
    for snapshot in snapshots:
        data = snapshot.to_dict()
        messages.append(
            MessageRecord(
                id=snapshot.id,
                ticket_id=str(ticket_id),
                author=_user_or_missing(data["author_uid"]),
                message=data["message"],
                created_at=data.get("created_at"),
            )
        )
    return messages


def add_message(user, ticket_id, message):
    ticket_ref = _db().collection("tickets").document(str(ticket_id))
    ticket_snapshot = ticket_ref.get()
    if not ticket_snapshot.exists:
        raise PermissionDenied("Você não tem acesso a esta dúvida.")
    ticket_data = ticket_snapshot.to_dict()
    if not ticket_is_visible(user, ticket_data):
        raise PermissionDenied("Você não tem acesso a esta dúvida.")
    if ticket_data.get("status") in {"RESOLVED", "CLOSED"}:
        raise ValidationError("Não é possível responder a uma dúvida encerrada.")
    message = message.strip()
    if not message:
        raise ValidationError("Escreva uma mensagem antes de enviar.")

    author_name = " ".join(
        part for part in (user.first_name, user.last_name) if part
    ) or user.username
    now = datetime.now(timezone.utc)
    batch = _db().batch()
    message_ref = ticket_ref.collection("messages").document()
    batch.create(
        message_ref,
        {
            "author_uid": user.uid,
            "author_name": author_name,
            "message": message,
            "created_at": now,
        },
    )
    new_status = (
        "ANSWERED"
        if user.tipo in {"MONITOR", "PROFESSOR", "COORDENADOR"}
        else "IN_PROGRESS"
    )
    batch.update(
        ticket_ref,
        {"status": new_status, "updated_at": now},
    )
    batch.commit()
