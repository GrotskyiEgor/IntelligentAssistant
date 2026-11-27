import os
import sys
from pathlib import Path

import django
from django.apps import apps


def setup_django():
    if apps.ready:
        return

    assistant_dir = Path(__file__).resolve().parents[2] / "assistant"
    if str(assistant_dir) not in sys.path:
        sys.path.insert(0, str(assistant_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assistant.settings")
    django.setup()


def tasks_for_day(day):
    setup_django()
    from core.models import Task

    return list(Task.objects.filter(day=day).order_by("time", "id"))


def create_task(data):
    setup_django()
    from core.tasks import create_task as save_task

    return save_task(data)


def update_task(task_id, data):
    setup_django()
    from core import tasks as core_tasks

    # Якщо в core.tasks є своя функція оновлення, користуємось нею
    if hasattr(core_tasks, "update_task"):
        return core_tasks.update_task(task_id, data)

    from core.models import Task

    task = Task.objects.get(pk=task_id)
    for field in ("title", "description", "day", "time", "difficulty"):
        if field in data:
            setattr(task, field, data[field])
    task.full_clean()
    task.save()
    return task
