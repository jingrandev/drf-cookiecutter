from django_celery_beat.models import CrontabSchedule
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask

PERIODIC_TASKS: dict[str, dict] = {}


def ensure_periodic_tasks():
    for task_name, task_config in PERIODIC_TASKS.items():
        schedule_type = None
        schedule = None

        crontab_config = task_config.get("crontab")
        interval_config = task_config.get("interval")
        if crontab_config and interval_config:
            continue

        if crontab_config:
            schedule_type = "crontab"
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=str(crontab_config.get("minute", "*")),
                hour=str(crontab_config.get("hour", "*")),
                day_of_week=str(crontab_config.get("day_of_week", "*")),
                day_of_month=str(crontab_config.get("day_of_month", "*")),
                month_of_year=str(crontab_config.get("month_of_year", "*")),
                timezone=str(crontab_config.get("timezone", "UTC")),
            )

        if interval_config:
            schedule_type = "interval"
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=int(interval_config["every"]),
                period=str(interval_config["period"]),
            )

        if schedule_type is None:
            continue

        create_defaults: dict = {
            "task": task_config["task"],
            "enabled": bool(task_config.get("enabled", True)),
        }
        if schedule_type == "crontab":
            create_defaults["crontab"] = schedule
            create_defaults["interval"] = None
        if schedule_type == "interval":
            create_defaults["interval"] = schedule
            create_defaults["crontab"] = None

        task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults=create_defaults,
        )

        if not created:
            update_fields: dict = {
                "task": task_config["task"],
            }
            if schedule_type == "crontab":
                update_fields["crontab"] = schedule
                update_fields["interval"] = None
            if schedule_type == "interval":
                update_fields["interval"] = schedule
                update_fields["crontab"] = None

            PeriodicTask.objects.filter(pk=task.pk).update(**update_fields)

        task.refresh_from_db(fields=["task", "enabled", "crontab", "interval"])
        print(f"[celery-beat] {task}")
