import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("app", broker="redis://redis:6379/0")
app.conf.result_backend = "redis://redis:6379/1"
app.conf.result_expires = 3600
app.conf.task_track_started = True
app.conf.update(
    broker_connection_retry_on_startup=True
)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

CELERY_WORKER_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(processName)s - %(message)s"
CELERY_WORKER_LOG_COLOR = False
CELERY_WORKER_LOG_LEVEL = "ERROR"


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
