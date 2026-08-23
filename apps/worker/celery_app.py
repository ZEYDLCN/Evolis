import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("evolis", broker=REDIS_URL, backend=REDIS_URL, include=["apps.worker.tasks"])

celery_app.conf.beat_schedule = {
    "generate-monthly-version-snapshots": {
        "task": "apps.worker.tasks.generate_monthly_snapshots",
        "schedule": 60 * 60 * 24,  # check daily; task itself only acts on month boundaries
    },
}
