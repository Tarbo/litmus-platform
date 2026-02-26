import os

from celery import Celery


broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("litmus", broker=broker_url, backend=broker_url)
celery_app.autodiscover_tasks(["app.workers"])
