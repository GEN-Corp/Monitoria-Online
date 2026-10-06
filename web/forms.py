from django import forms

from courses.models import Course
from users.models import User


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("code", "name", "description")


class MonitoringAssignmentForm(forms.Form):
    monitor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Monitor",
    )

    def __init__(self, *args, course, **kwargs):
        super().__init__(*args, **kwargs)
        already_assigned = course.monitorings.filter(
            status="ACTIVE"
        ).values_list("monitor_id", flat=True)
        self.fields["monitor"].queryset = (
            User.objects.filter(
                tipo=User.TipoUsuario.MONITOR,
                is_active=True,
            )
            .exclude(pk__in=already_assigned)
            .order_by("username")
        )
