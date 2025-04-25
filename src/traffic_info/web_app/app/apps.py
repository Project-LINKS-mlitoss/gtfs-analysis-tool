from django.apps import AppConfig
import subprocess
import os


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        if os.environ.get("CELERY_STARTED", None) != "true":
            os.environ["CELERY_STARTED"] = "true"
            subprocess.Popen(["celery", "-A", "app", "worker", "-l", "ERROR"])
