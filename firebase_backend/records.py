from dataclasses import dataclass, field
from datetime import datetime


ROLE_LABELS = {
    "ALUNO": "Aluno",
    "MONITOR": "Monitor",
    "PROFESSOR": "Professor",
    "COORDENADOR": "Coordenador",
}
TICKET_STATUS_LABELS = {
    "OPEN": "Aberto",
    "IN_PROGRESS": "Em atendimento",
    "ANSWERED": "Respondido",
    "RESOLVED": "Resolvido",
    "CLOSED": "Fechado",
}
PRIORITY_LABELS = {
    "LOW": "Baixa",
    "MEDIUM": "Média",
    "HIGH": "Alta",
}
MONITORING_STATUS_LABELS = {
    "ACTIVE": "Ativa",
    "INACTIVE": "Inativa",
}


@dataclass(frozen=True)
class FirebaseUser:
    uid: str
    username: str
    email: str
    first_name: str
    last_name: str
    tipo: str
    is_authenticated: bool = True
    is_anonymous: bool = False
    is_active: bool = True
    is_superuser: bool = False
    is_staff: bool = False

    @property
    def pk(self):
        return self.uid

    def get_tipo_display(self):
        return ROLE_LABELS.get(self.tipo, self.tipo)


@dataclass
class CourseRecord:
    id: str
    name: str
    code: str
    description: str
    active: bool
    created_by: str
    monitorings: list = field(default_factory=list)

    @property
    def pk(self):
        return self.id


@dataclass
class MonitoringRecord:
    id: str
    course_id: str
    monitor_id: str
    professor_id: str
    monitor: FirebaseUser
    professor: FirebaseUser
    status: str
    start_date: datetime
    end_date: datetime | None
    description: str

    def get_status_display(self):
        return MONITORING_STATUS_LABELS.get(self.status, self.status)


@dataclass
class MessageRecord:
    id: str
    ticket_id: str
    author: FirebaseUser
    message: str
    created_at: datetime


@dataclass
class TicketRecord:
    id: str
    student: FirebaseUser
    course: CourseRecord
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRecord] = field(default_factory=list)

    @property
    def pk(self):
        return self.id

    def get_status_display(self):
        return TICKET_STATUS_LABELS.get(self.status, self.status)

    def get_priority_display(self):
        return PRIORITY_LABELS.get(self.priority, self.priority)
