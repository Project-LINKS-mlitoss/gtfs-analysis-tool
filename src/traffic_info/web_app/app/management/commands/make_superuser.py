from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = "Creates a superuser from environment variables"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write(
                self.style.ERROR("Environment variables for superuser not set properly")
            )
            return

        if User.objects.filter(username=username).exists():
            User.objects.filter(username=username).delete()
            self.stdout.write(
                self.style.WARNING(f"Existing superuser {username} has been deleted")
            )

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superuser {username} created successfully")
            )
