from datetime import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.services.models import Service
from apps.staff.models import Doctor

from .models import Appointment, AppointmentSlot


class AppointmentCreateForm(forms.ModelForm):
    # дата нужна для фильтра слотов (в Appointment она хранится через slot.starts_at)
    preferred_date = forms.DateField(
        label="Дата",
        widget=forms.DateInput(attrs={"type": "date", "id": "date-input"}),
    )

    slot = forms.ModelChoiceField(
        label="Время записи",
        queryset=AppointmentSlot.objects.none(),
        empty_label="Выберите время",
        widget=forms.Select(attrs={"id": "slot-select"}),
    )

    class Meta:
        model = Appointment
        fields = (
            "service",
            "doctor",
            "full_name",
            "phone",
            "email",
            "preferred_date",
            "slot",
            "comment",
        )

    def __init__(
        self,
        *args,
        service_id=None,
        doctor_id=None,
        lock_service=False,
        lock_doctor=False,
        service_queryset=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        # queryset услуг (или ограничение по акции)
        self.fields["service"].queryset = service_queryset or Service.objects.filter(
            is_active=True,
            category__is_active=True,
        )

        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True)

        # initial дата: сегодня
        if not self.initial.get("preferred_date"):
            self.initial["preferred_date"] = timezone.localdate()

        # фиксируем услугу/врача при переходе из promo или doctors
        if service_id:
            self.fields["service"].initial = service_id
            if lock_service:
                self.fields["service"].widget = forms.HiddenInput()

        if doctor_id:
            self.fields["doctor"].initial = doctor_id
            if lock_doctor:
                self.fields["doctor"].widget = forms.HiddenInput()

        # ---- queryset слотов под текущие service + preferred_date ----
        service = None
        if self.data.get("service"):
            service = self.data.get("service")
        elif self.initial.get("service"):
            service = self.initial.get("service")

        preferred_date = None
        if self.data.get("preferred_date"):
            preferred_date = self.data.get("preferred_date")
        elif self.initial.get("preferred_date"):
            preferred_date = self.initial.get("preferred_date")

        qs = AppointmentSlot.objects.filter(is_active=True, is_booked=False)

        if service:
            qs = qs.filter(service_id=service)

        if preferred_date:
            # preferred_date может быть date или строкой YYYY-MM-DD
            if hasattr(preferred_date, "strftime"):
                date_str = preferred_date.strftime("%Y-%m-%d")
            else:
                date_str = str(preferred_date)
            qs = qs.filter(starts_at__date=date_str)

        self.fields["slot"].queryset = qs.order_by("starts_at")

        # ---- классы UI по умолчанию ----
        for name, f in self.fields.items():
            f.widget.attrs.setdefault(
                "class",
                "w-full rounded-2xl border px-4 py-3 text-slate-900 shadow-sm "
                "border-slate-200 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100"
            )

        self.fields["service"].widget.attrs.setdefault("id", "service-select")

    def clean_preferred_date(self):
        d = self.cleaned_data.get("preferred_date")
        if d and d < timezone.localdate():
            raise ValidationError("Нельзя выбрать прошедшую дату.")
        return d

    def clean_slot(self):
        slot = self.cleaned_data.get("slot")
        service = self.cleaned_data.get("service")

        if not slot:
            return slot

        # слот должен относиться к выбранной услуге
        if service and slot.service_id != service.id:
            raise ValidationError("Этот слот не относится к выбранной услуге.")

        if slot.is_booked:
            raise ValidationError("Этот слот уже занят. Выберите другое время.")

        if not slot.is_active:
            raise ValidationError("Этот слот недоступен. Выберите другое время.")

        # нельзя в прошлое
        if slot.starts_at and slot.starts_at < timezone.now():
            raise ValidationError("Нельзя записаться в прошлое время.")

        return slot