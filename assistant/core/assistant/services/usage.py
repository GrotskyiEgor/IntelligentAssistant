from django.db.models import F
from django.utils import timezone

from core.models import AppCommand, UsageLog


def log_action(action, text = ""):
    try:
        UsageLog.objects.create(kind="action", action=action, text=text[:255])
    except Exception as error:
        print(f"USAGE LOG ERROR: {error}", flush=True)


def log_app(app: AppCommand, action, text = ""):
    try:
        UsageLog.objects.create(
            kind="app", action=action, target=app.name, app=app, text=text[:255]
        )
        if action == "open":
            AppCommand.objects.filter(pk=app.pk).update(
                use_count=F("use_count") + 1,
                last_used_at=timezone.now(),
            )
    except Exception as error:
        print(f"USAGE LOG ERROR: {error}", flush=True)


def log_site(site, action = "open", text = ""):
    try:
        UsageLog.objects.create(
            kind="site", action=action, target=site.name, text=text[:255]
        )
    except Exception as error:
        print(f"USAGE LOG ERROR: {error}", flush=True)