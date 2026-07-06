from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.accounts.services import ROLE_GROUP_NAMES


class Command(BaseCommand):
    help = "Create default KP-HSLMS role groups."

    def handle(self, *args, **options):
        for group_name in ROLE_GROUP_NAMES.values():
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {group.name}"))
            else:
                self.stdout.write(f"Group already exists: {group.name}")

        self.stdout.write(self.style.SUCCESS("Role groups seeded successfully."))