from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()

celery_app = Celery(
    "macro_signal_engine",
    broker=str(settings.redis_url),
    include=["app.modules.events.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="ingestion",
    beat_schedule={
        "ingest-news-every-6-hours": {
            "task": "events.ingest_news",
            "schedule": crontab(minute=0, hour="*/6"),
            "options": {"queue": "ingestion"},
        },
    },
)


@setup_logging.connect
def configure_celery_logging(**kwargs: object) -> None:
    """
    Keep our structlog setup: Celery skips its own when this signal is handled.
    """
    configure_logging(
        json_logs=settings.log_format == "json",
        level=settings.log_level,
        log_sql=settings.log_sql,
    )
