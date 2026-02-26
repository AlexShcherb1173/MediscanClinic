"""
Forms for appointments application.

Includes AppointmentCreateForm:
- dynamic slot queryset based on selected service and date
- optional locking of service/doctor fields
- extra validation for selected slot
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.services.models import Service
from apps.staff.models import Doctor
from .models import Appointment, AppointmentSlot


class AppointmentCreateForm(forms.ModelForm):
    """
    Appointment creation form with dynamic slot selection.

    UX approach:
    - preferred_date and slot are stored as hidden inputs
    - slot queryset is calculated based on selected service and date
    - supports locking service/doctor when coming from service/doctor pages
    """

    preferred_date = forms.DateField(
        label="Дата",
        required=True,
        widget=forms.HiddenInput(),
    )

    slot = forms.ModelChoiceField(
        label="Время записи",
        queryset=AppointmentSlot.objects.none(),
        required=True,
        widget=forms.HiddenInput(),
        error_messages={
            "required": "Выберите слот для записи.",
            "invalid_choice": "Слот недоступен. Сначала выберите услугу и дату, затем выберите время из списка.",
        },
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
        **kwargs,
    ):
        """
        Initialize form and configure dynamic querysets.

        Args:
            service_id: optional preselected service id (e.g. from service detail page)
            doctor_id: optional preselected doctor id
            lock_service: if True, hide service field and make it not required
            lock_doctor: if True, hide doctor field and make it not required
            service_queryset: optional queryset for services (override default)
        """
        super().__init__(*args, **kwargs)

        self.fields["service"].queryset = service_queryset or Service.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True)

        selected_service = (
            self.data.get("service")
            or self.initial.get("service")
            or service_id
        )

        selected_date_raw = (
            self.data.get("preferred_date")
            or self.initial.get("preferred_date")
        )
        selected_date = parse_date(str(selected_date_raw)) if selected_date_raw else None

        qs = AppointmentSlot.objects.filter(is_active=True, is_booked=False)

        if selected_service:
            qs = qs.filter(service_id=selected_service)
        else:
            qs = AppointmentSlot.objects.none()

        if selected_date:
            qs = qs.filter(starts_at__date=selected_date)
        else:
            qs = AppointmentSlot.objects.none()

        self.fields["slot"].queryset = qs.order_by("starts_at")

        if service_id:
            self.fields["service"].initial = service_id
            if lock_service:
                self.fields["service"].widget = forms.HiddenInput()
                self.fields["service"].required = False

        if doctor_id:
            self.fields["doctor"].initial = doctor_id
            if lock_doctor:
                self.fields["doctor"].widget = forms.HiddenInput()
                self.fields["doctor"].required = False

        ui_class = (
            "w-full rounded-2xl border border-slate-200 px-4 py-3 "
            "text-slate-900 shadow-sm bg-white "
            "focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100"
        )
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", ui_class)

    def clean_slot(self):
        """
        Validate selected slot.

        Ensures:
        - slot is active and not booked
        - slot belongs to selected service (if service provided)
        - slot start time is not in the past
        """
        slot: AppointmentSlot = self.cleaned_data.get("slot")
        service = self.cleaned_data.get("service")

        if not slot:
            return slot

        if not slot.is_active:
            raise ValidationError("Этот слот недоступен. Выберите другой.")
        if slot.is_booked:
            raise ValidationError("Этот слот уже занят. Выберите другой.")

        if service and slot.service_id != service.id:
            raise ValidationError("Этот слот не относится к выбранной услуге.")

        if slot.starts_at and slot.starts_at < timezone.now():
            raise ValidationError("Нельзя записаться на прошедшее время.")

        return slot