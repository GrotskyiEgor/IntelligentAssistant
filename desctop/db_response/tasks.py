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
