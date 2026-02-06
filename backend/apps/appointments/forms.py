from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.services.models import Service
from apps.staff.models import Doctor
from .models import Appointment, AppointmentSlot


class AppointmentCreateForm(forms.ModelForm):
    # дата не хранится напрямую в Appointment (мы берём её из slot.starts_at),
    # но нужна для UI/фильтра слотов
    preferred_date = forms.DateField(
        label="Дата",
        required=True,
        widget=forms.HiddenInput(),  # управляем датой через календарь
    )

    slot = forms.ModelChoiceField(
        label="Время записи",
        queryset=AppointmentSlot.objects.none(),
        required=True,
        empty_label="Выберите время",
        widget=forms.Select(),
    )

    class Meta:
        model = Appointment
        fields = (
            "service",
            "doctor",
            "full_name",
            "phone",
            "email",
            "comment",
            "preferred_date",
            "slot",
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

        # услуги
        self.fields["service"].queryset = service_queryset or Service.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True)

        # определяем выбранные service/date для queryset слотов
        selected_service = (
            self.data.get("service") or self.initial.get("service") or service_id
        )
        selected_date = (
            self.data.get("preferred_date") or self.initial.get("preferred_date")
        )

        qs = AppointmentSlot.objects.filter(is_active=True, is_booked=False)

        if selected_service:
            qs = qs.filter(service_id=selected_service)

        if selected_date:
            # preferred_date приходит как "YYYY-MM-DD"
            qs = qs.filter(starts_at__date=selected_date)

        self.fields["slot"].queryset = qs.order_by("starts_at")

        # фиксация услуги (например, пришли из акции)
        if service_id:
            self.fields["service"].initial = service_id
            if lock_service:
                self.fields["service"].widget = forms.HiddenInput()
                self.fields["service"].required = False

        # фиксация врача (если нужно)
        if doctor_id:
            self.fields["doctor"].initial = doctor_id
            if lock_doctor:
                self.fields["doctor"].widget = forms.HiddenInput()
                self.fields["doctor"].required = False

        # классы UI
        for f in self.fields.values():
            f.widget.attrs.setdefault(
                "class",
                "w-full rounded-2xl border border-slate-200 px-4 py-3 "
                "text-slate-900 shadow-sm bg-white "
                "focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100"
            )

    def clean_slot(self):
        slot: AppointmentSlot = self.cleaned_data.get("slot")
        service = self.cleaned_data.get("service")

        if not slot:
            return slot

        if not slot.is_active:
            raise ValidationError("Этот слот недоступен. Выберите другой.")
        if slot.is_booked:
            raise ValidationError("Этот слот уже занят. Выберите другой.")

        # слот должен соответствовать услуге
        if service and slot.service_id != service.id:
            raise ValidationError("Этот слот не относится к выбранной услуге.")

        # нельзя в прошлое
        if slot.starts_at and slot.starts_at < timezone.now():
            raise ValidationError("Нельзя записаться на прошедшее время.")

        return slot

    def clean(self):
        cleaned = super().clean()
        slot: AppointmentSlot = cleaned.get("slot")
        if slot:
            # для дальнейшего сохранения в view
            cleaned["preferred_datetime"] = slot.starts_at
        return cleaned