from app.core.celery_app import celery_app


def test_tasks_are_discovered() -> None:
    celery_app.loader.import_default_modules()

    assert "events.ingest_news" in celery_app.tasks


def test_every_scheduled_task_exists() -> None:
    celery_app.loader.import_default_modules()

    schedule = celery_app.conf.beat_schedule
    assert schedule, "beat_schedule is empty: beat would run without doing anything"

    for name, entry in schedule.items():
        task_name = entry["task"]
        assert task_name in celery_app.tasks, (
            f"schedule entry {name!r} points at unknown task {task_name!r}"
        )


def test_scheduled_tasks_target_a_known_queue() -> None:
    known_queues = {"ingestion", "compute"}

    for name, entry in celery_app.conf.beat_schedule.items():
        queue = entry.get("options", {}).get(
            "queue", celery_app.conf.task_default_queue
        )
        assert queue in known_queues, (
            f"schedule entry {name!r} targets queue {queue!r}, which no worker consumes"
        )
