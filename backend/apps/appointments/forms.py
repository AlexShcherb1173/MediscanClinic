from datetime import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.services.models import Service
from apps.staff.models import Doctor
from .models import Appointment


class AppointmentCreateForm(forms.ModelForm):
    preferred_date = forms.DateField(
        label="Дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    preferred_time = forms.TimeField(
        label="Время",
        # ✅ оставляем TimeField, но рендерим как <select>
        widget=forms.Select(),
    )

    class Meta:
        model = Appointment
        fields = (
            "service",
            "doctor",
            "full_name",
            "phone",
            "comment",
        )

    def __init__(self, *args, service_id=None, doctor_id=None, lock_service=False, lock_doctor=False, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ активные queryset'ы
        self.fields["service"].queryset = Service.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True)

        # ✅ слоты будут подгружаться JS, но select должен быть валидным уже на старте
        self.fields["preferred_time"].choices = [("", "Выберите время")]

        # 🔒 фиксация услуги
        if service_id:
            self.fields["service"].initial = service_id
            if lock_service:
                self.fields["service"].widget = forms.HiddenInput()
                self.fields["service"].required = False

        # 🔒 фиксация врача
        if doctor_id:
            self.fields["doctor"].initial = doctor_id
            if lock_doctor:
                self.fields["doctor"].widget = forms.HiddenInput()
                self.fields["doctor"].required = False

        # ✅ классы для UI
        for f in self.fields.values():
            f.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-slate-200 focus:border-slate-400 focus:ring-0"
            )

    def clean(self):
        cleaned = super().clean()

        date = cleaned.get("preferred_date")
        time = cleaned.get("preferred_time")
        service = cleaned.get("service")
        doctor = cleaned.get("doctor")

        if not date or not time:
            return cleaned

        preferred_dt = timezone.make_aware(datetime.combine(date, time))

        if preferred_dt < timezone.now():
            raise ValidationError("Нельзя записаться в прошлое время.")

        # 🔴 конфликт по услуге
        if service and Appointment.objects.filter(service=service, preferred_datetime=preferred_dt).exists():
            raise ValidationError("На это время по выбранной услуге уже есть запись.")

        # 🔴 конфликт по врачу
        if doctor and Appointment.objects.filter(doctor=doctor, preferred_datetime=preferred_dt).exists():
            raise ValidationError("У врача уже есть запись на это время.")

        cleaned["preferred_datetime"] = preferred_dt
        return cleaned