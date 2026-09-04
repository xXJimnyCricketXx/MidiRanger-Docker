import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from app.models import Source, Settings


class Command(BaseCommand):
    help = 'Legt den Default-Source-Eintrag, die Settings-Singleton-Zeile und den Admin-Account an.'

    def handle(self, *args, **options):
        Source.objects.get_or_create(name='Unbekannt')
        Settings.load()

        username = os.environ.get('SEED_ADMIN_USERNAME', 'admin')
        password = os.environ.get('SEED_ADMIN_PASSWORD', 'admin123')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, password=password, email='')
            self.stdout.write(self.style.SUCCESS(f'Admin-Account "{username}" angelegt.'))
        else:
            self.stdout.write(f'Admin-Account "{username}" existiert bereits, übersprungen.')
