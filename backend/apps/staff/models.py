from django.db import models


class Specialty(models.Model):
    name = models.CharField("Специальность", max_length=120)

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    full_name = models.CharField("ФИО", max_length=150)
    photo = models.ImageField("Фото", upload_to="doctors/", blank=True)
    specialties = models.ManyToManyField(
        Specialty,
        related_name="doctors",
        verbose_name="Специальности",
        blank=True,
    )
    bio = models.TextField("Биография", blank=True)
    experience_years = models.PositiveIntegerField("Стаж (лет)", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"
        ordering = ("full_name",)

    def __str__(self):
        return self.full_name


class DoctorSchedule(models.Model):
    WEEKDAYS = (
        (0, "Понедельник"),
        (1, "Вторник"),
        (2, "Среда"),
        (3, "Четверг"),
        (4, "Пятница"),
        (5, "Суббота"),
        (6, "Воскресенье"),
    )

    doctor = models.ForeignKey(
        Doctor,
        related_name="schedules",
        on_delete=models.CASCADE,
        verbose_name="Врач",
    )
    weekday = models.PositiveSmallIntegerField("День недели", choices=WEEKDAYS)
    time_from = models.TimeField("С")
    time_to = models.TimeField("До")

    class Meta:
        verbose_name = "Расписание врача"
        verbose_name_plural = "Расписания врачей"
        ordering = ("doctor", "weekday", "time_from")

    def __str__(self):
        return f"{self.doctor} — {self.get_weekday_display()} {self.time_from}-{self.time_to}"
