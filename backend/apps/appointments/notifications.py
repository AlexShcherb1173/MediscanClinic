import logging
from dataclasses import dataclass

logger = logging.getLogger("appointments")


@dataclass(frozen=True)
class AppointmentNotification:
    full_name: str
    phone: str
    service_name: str
    preferred_datetime_iso: str


def notify_email(payload: AppointmentNotification) -> None:
    # заглушка
    logger.info(
        "[EMAIL] New appointment: %s, %s, service=%s, datetime=%s",
        payload.full_name,
        payload.phone,
        payload.service_name,
        payload.preferred_datetime_iso,
    )


def notify_telegram(payload: AppointmentNotification) -> None:
    # заглушка
    logger.info(
        "[TELEGRAM] New appointment: %s, %s, service=%s, datetime=%s",
        payload.full_name,
        payload.phone,
        payload.service_name,
        payload.preferred_datetime_iso,
    )