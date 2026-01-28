from __future__ import annotations

from .utils import get_busy_time_labels

from datetime import date, datetime, time, timedelta

from django import forms
from django.utils import timezone

from .models import Appointment


def generate_time_choices(
    start: time = time(8, 0),
    end: time = time(21, 0),
    step_minutes: int = 20,
) -> list[tuple[str, str]]:
    """
    Возвращает список time-слотов: [('08:00','09:00'), ...]
    end НЕ включительно (21:00 не попадёт, если end=21:00).
    """
    choices: list[tuple[str, str]] = []
    cur = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)

    while cur < end_dt:
        label = cur.strftime("%H:%M")
        choices.append((label, label))
        cur += timedelta(minutes=step_minutes)

    return choices


TIME_CHOICES = generate_time_choices()


class AppointmentCreateForm(forms.ModelForm):
    preferred_date = forms.DateField(
        label="Дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    preferred_time = forms.ChoiceField(
        label="Время",
        choices=TIME_CHOICES,
    )

    class Meta:
        model = Appointment
        fields = ("full_name", "phone", "comment")  # datetime собираем сами

    def __init__(self, *args, service_id: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._service_id = service_id
        # Если date уже есть (POST), берём из данных.
        # Если GET, можно оставить пусто — слоты придут по JS.
        d = None
        raw_date = None
        if self.data:
            raw_date = self.data.get("preferred_date")
        else:
            raw_date = self.initial.get("preferred_date")

        if raw_date:
            try:
                d = forms.DateField().clean(raw_date)
            except forms.ValidationError:
                d = None

        if service_id and d:
            busy = get_busy_time_labels(service_id, d)
            available = [(v, lbl) for (v, lbl) in TIME_CHOICES if v not in busy]
            self.fields["preferred_time"].choices = available

    def clean_preferred_date(self) -> date:
        d = self.cleaned_data["preferred_date"]
        today = timezone.localdate()
        if d < today:
            raise forms.ValidationError("Выберите дату не в прошлом.")
        if d > today + timedelta(days=90):
            raise forms.ValidationError("Можно записаться максимум на 90 дней вперёд.")
        return d

    def clean(self):
        cleaned = super().clean()
        d = cleaned.get("preferred_date")
        t_str = cleaned.get("preferred_time")
        if not d or not t_str:
            return cleaned

        # service_id будем прокидывать через form в view (см. ниже)
        service_id = getattr(self, "_service_id", None)
        if service_id:
            busy = get_busy_time_labels(service_id, d)
            if t_str in busy:
                self.add_error("preferred_time", "Этот слот уже занят. Выберите другой.")

        # собираем preferred_datetime как у тебя
        ...
        cleaned["preferred_datetime"] = aware_dt
        return cleaned