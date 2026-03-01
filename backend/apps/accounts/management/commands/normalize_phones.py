from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.accounts.utils import normalize_phone


class Command(BaseCommand):
    help = "Normalize all user phones to E.164"

    def handle(self, *args, **options):
        with transaction.atomic():
            for u in User.objects.exclude(phone__isnull=True).exclude(phone__exact=""):
                norm = normalize_phone(u.phone)

                # Detect duplicates after normalization
                if User.objects.filter(phone=norm).exclude(pk=u.pk).exists():
                    self.stdout.write(self.style.WARNING(
                        f"Duplicate after normalize: user_id={u.pk}, phone={u.phone} -> {norm}"
                    ))
                    continue

                if u.phone != norm:
                    u.phone = norm
                    u.save(update_fields=["phone"])

        self.stdout.write(self.style.SUCCESS("Done"))