import os

from ..services import precesses
from .base import Action, register
from ..services.apps import find_app
from ...utils.find_path import find_path

def _resolve_app(ctx, text, matched):
    app_text = text.replace(matched, "", 1).strip()
    if not app_text:
        ctx.speak("Не вказано назву програми")
        return None
    app = find_app(app_text)
    if not app:
        ctx.speak(f"Я не знайшла програму {app_text}")
    return app


@register
class OpenApp(Action):
    name = "open"

    def execute(self, ctx, text, matched):
        app = _resolve_app(ctx, text, matched)
        if not app:
            return

        ctx.speak(f"Відкриваю {app.name}")

        if not app.path:
            ctx.speak(f"Шукаю {app.name}")
            app.path = find_path(filename=app.name)
            if not app.path:
                ctx.speak(f"Я не знайшла шлях до {app.name}")
                return
            app.save()

        try:
            precesses.open_app(app.path)
        except Exception as error:
            print(f"Помилка запуску: {error}", flush=True)


@register
class CloseApp(Action):
    name = "close"

    def execute(self, ctx, text, matched):
        app = _resolve_app(ctx, text, matched)
        if not app:
            return
        if not app.path:
            ctx.speak(f"Я не знаю шлях до {app.name}")
            return

        ctx.speak(f"Закриваю {app.name}")
        precesses.close_app(os.path.basename(app.path))