"""
Формы приложения записей на приём.
Модуль содержит AppointmentCreateForm — форму создания записи, в которой:
- список слотов (AppointmentSlot) формируется динамически по выбранной услуге и дате;
- поля "услуга" и "врач" могут быть предзаполнены и (опционально) скрыты/заблокированы,
  если форма открыта со страницы услуги или врача;
- добавлена дополнительная валидация выбранного слота (активность, занятость, время в будущем).
"""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.accounts.utils import normalize_phone
from apps.services.models import Service
from apps.staff.models import Doctor

from .models import Appointment, AppointmentSlot


class AppointmentCreateForm(forms.ModelForm):
    """
    Форма создания записи на приём с динамическим выбором слота.
    Особенности UX:
    - preferred_date и slot хранятся в скрытых полях (HiddenInput);
    - queryset для slot рассчитывается в __init__ на основе выбранных service и preferred_date;
    - поддерживается сценарий "пришли со страницы услуги/врача":
      можно передать service_id / doctor_id и при необходимости скрыть поля
      (lock_service / lock_doctor), чтобы пользователь не менял контекст.
    """

    phone = forms.CharField(
        label="Телефон",
        required=True,
        max_length=32,
    )
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
        Инициализирует форму и настраивает динамические queryset'ы.
        Логика инициализации:
        - ограничивает услуги только активными (и с активной категорией);
        - ограничивает врачей только активными;
        - вычисляет выбранную услугу и дату (из self.data / initial / service_id);
        - формирует queryset слотов: активные слоты по услуге + по выбранной дате;
        - при переданных service_id/doctor_id выставляет initial значения;
          при lock_* скрывает соответствующее поле и снимает required;
        - добавляет единый CSS-класс всем не скрытым полям для консистентного UI.
        Параметры:
            service_id: ID услуги для предвыбора (например, со страницы услуги).
            doctor_id: ID врача для предвыбора (например, со страницы врача).
            lock_service: Если True — поле service скрывается и не является обязательным.
            lock_doctor: Если True — поле doctor скрывается и не является обязательным.
            service_queryset: Необязательный queryset услуг (если нужно переопределить фильтр по умолчанию).
        """
        super().__init__(*args, **kwargs)

        self.fields["service"].queryset = service_queryset or Service.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True)

        selected_service = self.data.get("service") or self.initial.get("service") or service_id

        selected_date_raw = self.data.get("preferred_date") or self.initial.get("preferred_date")
        selected_date = parse_date(str(selected_date_raw)) if selected_date_raw else None

        qs = AppointmentSlot.objects.filter(is_active=True)

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
        Валидирует выбранный слот времени.
        Проверяет, что слот:
        - существует в cleaned_data;
        - относится к будущему времени (по локальному времени, timezone-aware);
        - активен (is_active=True);
        - не занят (is_booked=False);
        - соответствует выбранной услуге (если услуга указана).
        Возвращает:
            AppointmentSlot: Провалидированный слот.
        Вызывает:
            ValidationError: если слот недоступен/занят/не относится к услуге/в прошлом.
        """
        slot: AppointmentSlot = self.cleaned_data.get("slot")
        service = self.cleaned_data.get("service")

        if not slot:
            return slot

        # прошедшее время — по локальному времени
        now_local = timezone.localtime(timezone.now())
        slot_local = timezone.localtime(slot.starts_at) if slot.starts_at else None
        if slot_local and slot_local < now_local:
            raise ValidationError("Нельзя записаться на прошедшую дату.")

        if not slot.is_active:
            raise ValidationError("Этот слот недоступен. Выберите другой.")

        if slot.is_booked:
            raise ValidationError("Этот слот уже занят. Выберите другой.")

        if service and slot.service_id != service.id:
            raise ValidationError("Этот слот не относится к выбранной услуге.")

        return slot

    def clean_phone(self):
        """
        Нормализует и валидирует номер телефона.
        Приводит введённый номер к формату E.164 (например, +79991234567)
        через normalize_phone(). При некорректном вводе возвращает понятную
        пользователю ошибку валидации.
        Возвращает:
            str: Нормализованный номер телефона в формате E.164.
        Вызывает:
            forms.ValidationError: если normalize_phone() вернул ValidationError.
        """
        ...
        raw = self.cleaned_data.get("phone", "")
        try:
            return normalize_phone(raw)
        except ValidationError as e:
            raise forms.ValidationError(e.message)
