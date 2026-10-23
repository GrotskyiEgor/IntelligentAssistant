import os

from core.models import AppGroup


def get_groups() -> list[tuple[str, list]]:
    groups = AppGroup.objects.prefetch_related("apps").order_by("id")
    return [(group.name, list(group.apps.all())) for group in groups]


def open_apps(apps) -> None:
    for app in apps:
        try:
            os.startfile(app.path)
        except OSError as error:
            print(f"Не вдалося запустити {app.name}: {error}", flush=True)