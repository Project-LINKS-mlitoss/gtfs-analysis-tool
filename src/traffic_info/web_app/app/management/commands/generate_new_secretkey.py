import secrets
import string
import os
from django.core.management.base import BaseCommand
from pathlib import Path


class Command(BaseCommand):
    help = "Generates a new Django SECRET_KEY and writes it to .env file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--length", type=int, default=64, help="Length of the generated SECRET_KEY"
        )
        parser.add_argument(
            "--env-file",
            type=str,
            default="../.env",
            help="Path to the .env file, relative to manage.py",
        )
        parser.add_argument(
            "--no-punctuation",
            action="store_true",
            help="Exclude punctuation characters from the SECRET_KEY",
        )

    def handle(self, *args, **options):
        length = options["length"]
        env_file = options["env_file"]
        use_punctuation = not options["no_punctuation"]

        if use_punctuation:
            alphabet = string.ascii_letters + string.digits + string.punctuation
        else:
            alphabet = string.ascii_letters + string.digits

        secret_key = "".join(secrets.choice(alphabet) for i in range(length))

        env_path = Path(env_file)
        print(env_path)
        print(secret_key)

        self._write_to_env(env_path, secret_key)

        self.stdout.write(
            self.style.SUCCESS(
                f"New SECRET_KEY has been generated and written to {env_path} file."
            )
        )
        self.stdout.write(f"Key length: {length} characters")

    def _write_to_env(self, env_path, secret_key):
        if not env_path.exists():
            env_path.parent.mkdir(parents=True, exist_ok=True)
            with open(env_path, "w") as f:
                f.write(f'SECRET_KEY="{secret_key}"\n')
            return

        with open(env_path, "r") as f:
            lines = f.readlines()

        secret_key_found = False
        new_lines = []

        for line in lines:
            if line.strip().startswith("SECRET_KEY="):
                new_lines.append(f'SECRET_KEY="{secret_key}"\n')
                secret_key_found = True
            else:
                new_lines.append(line)

        if not secret_key_found:
            new_lines.append(f'SECRET_KEY="{secret_key}"\n')

        with open(env_path, "w") as f:
            f.writelines(new_lines)
