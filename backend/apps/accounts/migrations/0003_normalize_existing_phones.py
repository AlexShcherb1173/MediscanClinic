from __future__ import annotations

from django.db import migrations, models


def noop_reverse(apps, schema_editor):
    pass


def normalize_phones_forward(apps, schema_editor):
    import re
    import phonenumbers

    User = apps.get_model("accounts", "User")

    def to_e164(raw: str) -> str | None:
        if raw is None:
            return None
        value = str(raw).strip()
        if not value:
            return None
        value = re.sub(r"[^\d+]", "", value)
        try:
            parsed = phonenumbers.parse(value, None if value.startswith("+") else "RU")
            if not phonenumbers.is_valid_number(parsed):
                return None
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            return None

    # Важно: пишем через SQL (обходим model validation и save())
    with schema_editor.connection.cursor() as cursor:
        rows = list(
            User.objects
            .all()
            .values_list("id", "phone")
        )

        for user_id, raw_phone in rows:
            # 1) сохраняем исходник
            cursor.execute(
                "UPDATE accounts_user SET phone_raw = %s WHERE id = %s",
                [raw_phone, user_id],
            )

            # 2) нормализуем
            e164 = to_e164(raw_phone)

            if not e164:
                # некорректный -> отключаем и ставим NULL
                cursor.execute(
                    "UPDATE accounts_user SET phone = NULL, is_active = FALSE WHERE id = %s",
                    [user_id],
                )
                continue

            # 3) проверяем дубликат УЖЕ в БД (чтобы не словить UniqueViolation)
            cursor.execute(
                "SELECT 1 FROM accounts_user WHERE phone = %s AND id <> %s LIMIT 1",
                [e164, user_id],
            )
            exists = cursor.fetchone() is not None

            if exists:
                # дубликат после нормализации -> отключаем и ставим NULL
                cursor.execute(
                    "UPDATE accounts_user SET phone = NULL, is_active = FALSE WHERE id = %s",
                    [user_id],
                )
                continue

            # 4) записываем нормализованный
            cursor.execute(
                "UPDATE accounts_user SET phone = %s WHERE id = %s",
                [e164, user_id],
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_alter_user_managers_remove_user_username_and_more"),
    ]

    operations = [
        # 1) добавляем поле под исходное значение
        migrations.AddField(
            model_name="user",
            name="phone_raw",
            field=models.CharField(
                max_length=64,
                null=True,
                blank=True,
                verbose_name="Телефон (как был введён)",
            ),
        ),
        # 2) временно разрешаем NULL, чтобы разрулить дубликаты
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(
                max_length=24,
                unique=True,
                null=True,
                blank=True,
                verbose_name="Телефон",
                db_index=True,
            ),
        ),
        migrations.RunPython(normalize_phones_forward, noop_reverse),
    ]