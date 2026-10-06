from django import forms


class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    email = forms.EmailField(label="E-mail")
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput,
        label="Senha",
    )
    password_confirm = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput,
        label="Confirmar senha",
    )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("password")
            and cleaned_data.get("password_confirm")
            and cleaned_data["password"] != cleaned_data["password_confirm"]
        ):
            self.add_error("password_confirm", "As senhas não coincidem.")
        return cleaned_data


class CourseForm(forms.Form):
    code = forms.RegexField(
        regex=r"^[A-Za-z0-9_-]{1,20}$",
        max_length=20,
        label="Código",
        error_messages={
            "invalid": "Use até 20 letras, números, hífens ou sublinhados."
        },
    )
    name = forms.CharField(max_length=200, label="Nome")
    description = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label="Descrição",
    )


class MonitoringAssignmentForm(forms.Form):
    monitor = forms.ChoiceField(label="Monitor")

    def __init__(self, *args, monitors, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["monitor"].choices = [
            (monitor.uid, monitor.username) for monitor in monitors
        ]
